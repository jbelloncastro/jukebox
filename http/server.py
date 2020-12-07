from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse
from aiohttp_sse import EventSourceResponse, sse_response

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate, Proxy

import pystache

import json

from jukebox.queue import Queue, Track
from jukebox.search import YouTubeFinder

from functools import partial

finder = None
queue = None
page = None

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


async def initialize():
    (_, protocol) = await connect_and_authenticate(bus="SESSION")
    queue = Queue(protocol)
    await queue.registerHandler()
    finder = YouTubeFinder()
    return (finder, queue)

def render(state):
    renderer = pystache.renderer.Renderer()
    with open("../html/index.mustache", "r") as f:
        template = f.read()
        page = pystache.parse(template)
        return renderer.render(page, state)

def queueState():
    return queue.queue

async def getRoot(request):
    # isMobile = False
    # agent = request.headers.get('User-agent', None)
    # if agent:
    #     isMobile = 'Mobile' in agent

    state = queueState()
    # state['mobile'] = isMobile

    # Set 'coming next' elements queue position
    pos = 2
    for item in state[1:]:
        item.pos = pos
        pos += 1
    text = render(state)
    return web.Response(text=text, content_type="text/html")


async def getTracks(request):
    state = queueState()
    return json_response(data=state,
                         headers={'ETag' : queue.hash.hexdigest()},
                         dumps=encodeQueue)

async def addTrack(request):
    query = await request.text()
    if not query:
        return web.HTTPBadRequest(text="Illegal search query")

    result = finder.search(query)
    await queue.addTrack(result)

    return await getTracks(request)

async def notifyChange(request):
    async with sse_response(request) as response:
        events = asyncio.Queue()
        queue.addListener(events)
        try:
            while not response.task.done():
                payload = encodeQueue(await events.get())
                await response.send(payload)
                events.task_done()
        finally:
            queue.removeListener(events)
    return response


# Start
loop = asyncio.get_event_loop()
(finder, queue) = loop.run_until_complete(initialize())

app = web.Application()
app.add_routes(
    [
        web.get("/", getRoot),
        web.get("/tracks", getTracks),
        web.post("/tracks", addTrack),
        web.get("/changes", notifyChange),
        web.static("/assets", "/home/jbellon/test/ytube-dl/jukebox/html"),
    ]
)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port="8080")
