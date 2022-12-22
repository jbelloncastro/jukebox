# Perform YouTube video searches
from youtube_dl import YoutubeDL

from jukebox.server.tracklist import Track


class SearchError(Exception):
    def __init__(self):
        pass

class YouTubeFinder:
    def __init__(self):
        self.query_format = "ytsearch1:{}"

        options = {"format": "bestaudio/best", "simulate": True}

        self.downloader = YoutubeDL(options)

    def search(self, query):
        "Search YouTube for the first result and returns information "
        "for the highest quality, audio-only result"

        def audioBitrate(f):
            "Sorts by audio bitrate prioritizing audio-only results"
            bitrate = f.get("abr", 0)
            isVideo = f.get("vcodec", "none") != "none"
            return (0 if isVideo else 1, bitrate)

        query = self.query_format.format(query)
        results = self.downloader.extract_info(query, False)
        results = results.get("entries", list())
        if len(results) == 0:
            raise SearchError()
        else:
            result = results[0]

        selected = max(result["formats"], key=audioBitrate)

        # If media is fragmented, we must use 'fragment_base_url' instead of 'url'
        url_key = "url"
        fragments = selected.get("fragments", [])
        if len(fragments) > 0:
            url_key = "fragment_base_url"
        url = selected[url_key]

        return Track(
            result["id"], result["title"], result["thumbnail"], result["tags"], url,
        )
