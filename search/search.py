# Perform YouTube video searches
import youtube_dl

from track_metadata import Track


class YouTubeFinder:
    def __init__(self):
        self.query_format = "ytsearch1:{}"

        options = {"format": "bestaudio/best", "simulate": True}

        self.downloader = youtube_dl.YoutubeDL(options)

    def search(self, query):
        "Search YouTube for the first result and returns information "
        "for the highest quality, audio-only result"

        def audioBitrate(f):
            "Sorts by audio bitrate prioritizing audio-only results"
            return f["abr"] if f["vcodec"] == "none" else 0

        query = self.query_format.format(query)
        results = self.downloader.extract_info(query, False)
        result = results["entries"][0]
        selected = max(result["formats"], key=audioBitrate)

        return Track(
            result["id"],
            result["title"],
            result["thumbnail"],
            result["tags"],
            selected["url"],
        )
