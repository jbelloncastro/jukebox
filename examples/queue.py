#!/usr/bin/python3
from jeepney.integrate.blocking import connect_and_authenticate

from jukebox.tracklist import Queue
from jukebox.search import YouTubeFinder

with connect_and_authenticate(bus="SESSION") as connection:
    finder = YouTubeFinder()
    queue = Queue(connection)
    try:
        while True:
            query = input("ytsearch: ")
            if len(query) > 0:
                result = finder.search(query)
                queue.addTrack(result)
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass

