
from jeepney.integrate.blocking import Proxy

import hashlib

from jukebox.mpris import Player, TrackList
from jukebox.mpris.properties import PlayerProperties, TrackListProperties

class Track:
    def __init__(self, tid, title, caption, tags, url):
        self.id = tid
        self.title = title
        self.caption = caption
        self.tags = tags
        self.url = url

class Queue:
    def __init__(self, connection):
        self.hash = hashlib.sha1()
        self.tracklist = Proxy(TrackList(), connection)
        self.player = Proxy(Player(), connection)
        self.playerProperties = Proxy(PlayerProperties(), connection)

        self.queue = []

        # Subscribe to /org/mpris/MediaPlayer2/Metadata property changes,
        # which mean the song has changed

    def addTrack(self, track):
        self.queue.append(track)
        self.hash.update(str.encode(track.id))

        # Resume playing if necessary
        status = self.playerProperties.PlaybackStatus()[0]
        resume = status == ("s", "Stopped")
        
        trackIdTail = '/org/mpris/MediaPlayer2/TrackList/Append'
        reply = self.tracklist.AddTrack(track.url, trackIdTail, resume)
        print(reply)
        return self.queue

    def handleSongCompleted(self):
        pass
