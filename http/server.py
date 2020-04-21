from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate

import pystache

import json

from jukebox.queue import Queue, Track
from jukebox.search import YouTubeFinder

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


finder = YouTubeFinder()

loop = asyncio.get_event_loop()
(transport, protocol) = loop.run_until_complete(connect_and_authenticate(bus="SESSION"))
queue = Queue(protocol)

page = None
def render(state):
    renderer = pystache.renderer.Renderer()
    with open("../html/index.mustache", "r") as f:
        template = f.read()
        page = pystache.parse(template)
        return renderer.render(page, state)


async def getRoot(request):
    state = {}
    if len(queue.queue) > 0:
        state["current"] = queue.queue[0]
    if len(queue.queue) > 1:
        state["next"] = queue.queue[1:]

    print(json.dumps(state, cls=TrackEncoder))
    text = render(state)
    return web.Response(text=text, content_type="text/html")


async def getTracks(request):
    encoder = lambda body : json.dumps(body, cls=TrackEncoder)
    return json_response(data=queue.queue,
                         headers={'ETag' : queue.hash.hexdigest()},
                         dumps=encoder)

async def addTrack(request):
    query = await request.text()
    if not query:
        return web.HTTPBadRequest(text="Illegal search query")

    result = finder.search(query)
    await queue.addTrack(result)

    return web.Response(headers={'ETag' : queue.hash.hexdigest()})

async def sendFile(name, request):
    return FileResponse(path="../html/{}".format(name))

app = web.Application()
app.add_routes(
    [
        web.get("/", getRoot),
        web.get("/tracks", getTracks),
        web.post("/tracks", addTrack),
        web.get("/submit.js", partial(sendFile,'submit.js')),
        web.get("/layout.css", partial(sendFile,'layout.css')),
    ]
)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port="8080")
