from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse
from aiohttp_sse import EventSourceResponse, sse_response

import asyncio

from pathlib import Path
import pystache

import json

from jukebox.server.tracklist import Queue, Track, TrackEncoder
from jukebox.server.search import YouTubeFinder

from functools import partial

import signal

from itertools import count

class Server:
    rootdir = Path(__file__).parent / ".."
    assetsdir = rootdir / "html"
    pagefile = assetsdir / "index.mustache"

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
        renderer = pystache.renderer.Renderer()
        with Server.pagefile.open("r") as f:
            template = f.read()
            page = pystache.parse(template)
            result = renderer.render(page, state)
            return result

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
        query = await request.text()
        if not query:
            return web.HTTPBadRequest(text="Illegal search query")

        result = self.finder.search(query)
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


def main_func():
    loop = asyncio.get_event_loop()
    for s in {signal.SIGINT, signal.SIGTERM}:
        loop.add_signal_handler(s, lambda: loop.stop())

    server = Server("0.0.0.0", "8080")
    try:
        loop.create_task(server.start())
        print("Running. Press Ctrl-C to exit.")
        loop.run_forever()
    finally:
        print("Exiting...")
        loop.run_until_complete(server.stop())


if __name__ == "__main__":
    main_func()
