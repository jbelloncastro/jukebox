from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse
from aiohttp_sse import EventSourceResponse, sse_response

import asyncio

from concurrent.futures import ThreadPoolExecutor

from itertools import count

import json

from jukebox.server.tracklist import Queue, Track, TrackEncoder
from jukebox.server.search import YouTubeFinder

from functools import partial

from pathlib import Path

import jinja2

import signal

class Server:
    rootdir = Path(__file__).parent / ".."
    assetsdir = rootdir / "html"
    pagefile = "index.template"

    def __init__(self, host, port):
        self.host = host
        self.port = port

        # Performs video searches on YouTube
        self.finder = YouTubeFinder()

        # List of tracks and DBus communication with media player
        self.queue = None

        # Web application server
        app = web.Application()
        app.add_routes(
            [
                web.get("/", lambda req: self.getRoot(req)),
                web.get("/tracks", lambda req: self.getTracks(req)),
                web.post("/tracks", lambda req: self.addTrack(req)),
                web.delete("/tracks/{track_id}", lambda req: self.removeTrack(req)),
                web.get("/changes", lambda req: self.notifyChange(req)),
                web.static("/assets", Server.assetsdir),
            ]
        )
        self.runner = web.AppRunner(app)

        # Will be used to process search requests in the background
        # Make sure each worker thread has an event loop
        self.pool = ThreadPoolExecutor(initializer=lambda:
                asyncio.set_event_loop(asyncio.new_event_loop())
                )

        template_dir = ""
        self.env = jinja2.Environment(
                        loader=jinja2.FileSystemLoader(searchpath=Server.assetsdir),
                        trim_blocks=True,
                        lstrip_blocks=True)
        self.template = self.env.get_template(Server.pagefile)

    async def start(self):
        # Setup DBus connection and server-sent-event queue
        self.queue = await Queue.create()

        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

    async def stop(self):
        await self.queue.cleanup()
        await self.runner.cleanup()

    def render(self, state):
        return self.template.render(current=state.get('current', None),
                                    next=state.get('next', list()),
                                    mobile=state.get('isMobile', False))

    async def getRoot(self, request):
        # isMobile = False
        # agent = request.headers.get('User-agent', None)
        # if agent:
        #     isMobile = 'Mobile' in agent

        state = {}
        if len(self.queue.tracks) > 0:
            state['current'] = self.queue.tracks[0]
        if len(self.queue.tracks) > 1:
            state['next'] = self.queue.tracks[1:]
            # Set queue position
            for pos, item in zip(count(2), state['next']):
                item.pos = pos

        # state['mobile'] = isMobile

        text = self.render(state)
        return web.Response(text=text, content_type="text/html")

    async def getTracks(self, request):
        return json_response(
            data=self.queue.tracks,
            headers={"ETag": str(self.queue.uuid)},
            dumps=lambda d: json.dumps(d, cls=TrackEncoder),
        )

    async def addTrack(self, request):
        def queryInBackground(self, request):
            # This is run in a different thread
            loop = asyncio.get_event_loop()
            query = loop.run_until_complete(request.text())
            if not query:
                return web.HTTPBadRequest(text="Illegal search query")
            print("Run background")
            return self.finder.search(query)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.pool, queryInBackground, self, request)

        await self.queue.addTrack(result)
        return await self.getTracks(request)

    async def removeTrack(self, request):
        try:
            track_id = int(request.match_info['track_id'])
            await self.queue.removeTrack(track_id)
        except ValueError:
            return web.Response(status=400, body="Invalid track id")
        return web.Response(status=200)

    async def notifyChange(self, request):
        async with sse_response(request) as response:
            events = asyncio.Queue()
            self.queue.addListener(events)
            response.content_type = "application/json"
            try:
                payload = await events.get()
                while not response.task.done() and payload:
                    body = json.dumps(payload, cls=TrackEncoder)
                    await response.send(body)
                    events.task_done()
                    payload = await events.get()
            finally:
                self.queue.removeListener(events)
        return response

    @classmethod
    def run(address="0.0.0.0", port=8080):
        loop = asyncio.get_event_loop()
        for s in {signal.SIGINT, signal.SIGTERM}:
            loop.add_signal_handler(s, lambda: loop.stop())

        server = Server("0.0.0.0", str(port))
        try:
            loop.create_task(server.start())
            print("Running. Press Ctrl-C to exit.")
            loop.run_forever()
        finally:
            print("Exiting...")
            loop.run_until_complete(server.stop())


if __name__ == "__main__":
    Server.run()
