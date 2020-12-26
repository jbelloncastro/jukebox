from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse
from aiohttp_sse import EventSourceResponse, sse_response

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate, Proxy

from pathlib import Path
import pystache

import json

from jukebox.server.tracklist import Queue, Track
from jukebox.server.search import YouTubeFinder

from functools import partial

class TrackEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Track):
            return {
                    'id' : obj.id,
                    'title' : obj.title,
                    'caption' : obj.caption
                    }
        return super().default(obj)

def encodeQueue(queue):
    return json.dumps(queue, cls=TrackEncoder)

class Server:
    rootdir = Path(__file__).parent / '..'
    assetsdir = rootdir / 'html'
    pagefile = assetsdir / 'index.mustache'

    def __init__(self, aioloop, host, port):
        self.aioloop = aioloop
        self.host = host
        self.port = port

        self.finder = YouTubeFinder()
        self.queue = None

        self.app = web.Application()
        self.app.add_routes(
            [
                web.get("/", lambda req: self.getRoot(req)),
                web.get("/tracks", lambda req: self.getTracks(req)),
                web.post("/tracks", lambda req: self.addTrack(req)),
                web.get("/changes", lambda req: self.notifyChange(req)),
                web.static("/assets", Server.assetsdir),
            ]
        )

    def start(self):
        async def init(server):
            "Hides initialization function from Server interface"
            (_, protocol) = await connect_and_authenticate(bus="SESSION")
            queue = Queue(protocol)
            await queue.registerHandler()
            server.queue = queue

        self.aioloop.run_until_complete(init(self))

    def run(self):
        web.run_app(self.app, host=self.host, port=self.port)

    def render(self, state):
        renderer = pystache.renderer.Renderer()
        with Server.pagefile.open('r') as f:
            template = f.read()
            page = pystache.parse(template)
            return renderer.render(page, state)
    
    def queueState(self):
        return self.queue.queue
    
    async def getRoot(self, request):
        # isMobile = False
        # agent = request.headers.get('User-agent', None)
        # if agent:
        #     isMobile = 'Mobile' in agent
    
        state = self.queueState()
        # state['mobile'] = isMobile
    
        # Set 'coming next' elements queue position
        pos = 2
        for item in state[1:]:
            item.pos = pos
            pos += 1
        text = self.render(state)
        return web.Response(text=text, content_type="text/html")
    
    
    async def getTracks(self, request):
        state = self.queueState()
        return json_response(data=state,
                             headers={'ETag' : self.queue.hash.hexdigest()},
                             dumps=encodeQueue)
    
    async def addTrack(self, request):
        query = await request.text()
        if not query:
            return web.HTTPBadRequest(text="Illegal search query")
    
        result = self.finder.search(query)
        await self.queue.addTrack(result)
    
        return await self.getTracks(request)
    
    async def notifyChange(self, request):
        async with sse_response(request) as response:
            events = asyncio.Queue()
            self.queue.addListener(events)
            try:
                while not response.task.done():
                    payload = encodeQueue(await events.get())
                    await response.send(payload)
                    events.task_done()
            finally:
                self.queue.removeListener(events)
        return response


def main_func():
    loop = asyncio.get_event_loop()
    server = Server(loop, "0.0.0.0", "8080")
    server.start()
    server.run()

if __name__ == "__main__":
    main_func()
