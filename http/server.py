from aiohttp import web
from aiohttp.web_response import json_response
from aiohttp.web_fileresponse import FileResponse

import asyncio

from jeepney.integrate.asyncio import connect_and_authenticate

import pystache

import json

from jukebox.queue import Queue, Track
from jukebox.search import YouTubeFinder

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
    # name = request.match_info.get("name", "Anonymous")
    state = {
        "current": {
            "thumbnail": "https://i.ytimg.com/vi/uE-1RPDqJAY/hqdefault.jpg",
            "title": "They are taking the hobbits to isengart",
            "uploader": "unknown",
            "tags": [],
        },
        "next": [],
    }
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

async def submitJS(request):
    return FileResponse(path="../html/submit.js")

app = web.Application()
app.add_routes(
    [
        web.get("/", getRoot),
        web.get("/tracks", getTracks),
        web.post("/tracks", addTrack),
        web.get("/submit.js", submitJS),
    ]
)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port="8080")
