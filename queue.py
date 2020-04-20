
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
    def __init__(self, protocol):
        self.hash = hashlib.sha1()
        self.protocol = protocol

        self.queue = []

        # Subscribe to /org/mpris/MediaPlayer2/Metadata property changes,
        # which mean the song has changed

    async def addTrack(self, track):
        self.queue.append(track)
        self.hash.update(str.encode(track.id))

        # Resume playing if necessary
        playerStatus = PlayerProperties().PlaybackStatus()
        status = await self.protocol.send_message(playerStatus)
        resume = status[0] == ("s", "Stopped")
        
        trackIdTail = '/org/mpris/MediaPlayer2/TrackList/Append'
        addTrack = TrackList().AddTrack(track.url, trackIdTail, resume)
        await self.protocol.send_message(addTrack)
        return self.queue

    def handleSongCompleted(self):
        pass
