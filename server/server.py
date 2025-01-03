from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse
from aiohttp_sse import EventSourceResponse, sse_response

import asyncio

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress

from itertools import count

import json

from jukebox.server.tracklist import Queue, QueueState, Track, TrackEncoder
from jukebox.server.search import YouTubeFinder

from functools import partial

from pathlib import Path

import jinja2
import os

class Server:
    rootdir = Path(__file__).parent / ".."
    assetsdir = rootdir / "html"
    pagefile = "index.template"

    def __init__(self, host, port, queue):
        self.host = host
        self.port = port

        # Performs video searches on YouTube
        self.finder = YouTubeFinder()

        # List of tracks and DBus communication with media player
        self.queue = queue

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

        self.template_mtime = 0
        self.reload_template()

    def reload_template(self):
        curr_mtime = os.stat(Server.assetsdir / Server.pagefile).st_mtime
        if self.template_mtime < curr_mtime:
            self.template_mtime = curr_mtime
            self.template = self.env.get_template(Server.pagefile)

    async def start(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

    async def stop(self):
        await self.queue.cleanup()
        await self.runner.cleanup()

    def render(self, state):
        self.reload_template()
        return self.template.render(current=state.get('current', None),
                                    next=state.get('next', list()),
                                    mobile=state.get('isMobile', False))

    async def getRoot(self, request):
        # isMobile = False
        # agent = request.headers.get('User-agent', None)
        # if agent:
        #     isMobile = 'Mobile' in agent

        state = QueueState(self.queue)
        result = {}
        if len(state.tracks) > 0:
            result['current'] = state.tracks[0]
        if len(state.tracks) > 1:
            result['next'] = state.tracks[1:]
            # Set queue position
            for pos, item in zip(count(2), result['next']):
                item.pos = pos

        # state['mobile'] = isMobile

        text = self.render(result)
        return web.Response(text=text, content_type="text/html")

    async def getTracks(self, request):
        state = QueueState(self.queue)
        return json_response(
            data=state.tracks,
            headers={"ETag": state.etag},
            dumps=lambda d: json.dumps(d, cls=TrackEncoder),
        )

    async def addTrack(self, request):
        def queryInBackground(self, request):
            # This is run in a different thread
            loop = asyncio.get_event_loop()
            query = loop.run_until_complete(request.text())
            if not query:
                raise web.HTTPBadRequest(text="Illegal search query")
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
        with suppress(ConnectionResetError):
            async with sse_response(request) as response, self.queue.createListener() as events:
                response.content_type = "application/json"
                # Returns None when the server is shutting down
                while (payload := await events.get()) != None:
                    body = json.dumps(payload, cls=TrackEncoder)
                    await response.send(body)
                    events.task_done()
                events.task_done()
        return response

