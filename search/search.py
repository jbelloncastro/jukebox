
# Perform YouTube video searches
import youtube_dl


class Result:
    def __init__(self, title, caption, tags, url):
        self.title = title
        self.caption = caption
        self.tags = tags
        self.url = url


class YouTubeFinder:
    def __init__(self):
        self.query_format = "ytsearch1:{}"

        options = {
            'format': 'bestaudio/best',
            'simulate': True
        }

        self.downloader = youtube_dl.YoutubeDL(options)

    def search(self, query):
        def audioBitrate(f):
            return f['abr'] if f['vcodec'] == 'none' else 0

        query = self.query_format.format(query)
        results = self.downloader.extract_info(query, False)
        result = results['entries'][0]
        selected = max(result['formats'], key=audioBitrate)

        return Result(result['title'],
                      result['thumbnail'],
                      result['tags'],
                      selected['url'])
