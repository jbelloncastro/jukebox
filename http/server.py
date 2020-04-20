from aiohttp import web

import pystache

page = None
renderer = pystache.renderer.Renderer()
with open("../html/index.mustache", "r") as f:
    template = f.read()
    print(template)
    page = pystache.parse(template)


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
    text = renderer.render(page, state)
    print (text)
    return web.Response(text=text, content_type="text/html")


async def getTracks(request):
    name = request.match_info.get("name", "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


async def addTrack(request):
    name = request.match_info.get("name", "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


app = web.Application()
app.add_routes(
    [
        web.get("/", getRoot),
        web.get("/tracks", getTracks),
        web.post("/tracks", addTrack),
    ]
)

# Default: http://localhost:8080
if __name__ == "__main__":
    web.run_app(app)
