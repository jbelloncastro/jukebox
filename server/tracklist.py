from asyncio import get_event_loop, gather

from functools import partial

from itertools import dropwhile

from jeepney.integrate.asyncio import Proxy
from jeepney.bus_messages import MatchRule, DBus

from jukebox.dbus.org_mpris_MediaPlayer2 import Player, TrackList
from jukebox.dbus.properties import PlayerProperties, TrackListProperties
from jukebox.dbus.signals import PropertiesChanged
from jukebox.server.track_metadata import parseTrackMetadata

from json import JSONEncoder

from uuid import uuid4


class Track:
    def __init__(self, tid, title, caption, tags, url):
        self.id = tid
        self.title = title
        self.caption = caption
        self.tags = tags
        self.url = url

    def matchesUrl(self, url):
        return self.url == url


class QueueState:
    def __init__(self, queue):
        self.tracks = queue.queue.copy()
        self.etag = str(queue.uuid.hex)


class Queue:
    def __init__(self, protocol):
        self.uuid = uuid4()
        self.protocol = protocol

        # List of tracks
        self.queue = []
        # Clients subscribed to song change events
        self.listeners = set()

    def notifyListChange(self):
        # Regenerate etag
        self.uuid = uuid4()

        state = QueueState(self)
        return [client.put(state) for client in self.listeners]

    async def addTrack(self, track):
        # Resume playing if necessary
        playerStatus = PlayerProperties().PlaybackStatus()
        status = await self.protocol.send_message(playerStatus)
        resume = status[0] == ("s", "Stopped")

        trackIdTail = "/org/mpris/MediaPlayer2/TrackList/Append"
        addTrack = TrackList().AddTrack(track.url, trackIdTail, resume)

        self.queue.append(track)
        sequence = self.notifyListChange()
        sequence.append(self.protocol.send_message(addTrack))
        await gather(*sequence)
        return self.queue

    def addListener(self, eventQueue):
        self.listeners.add(eventQueue)

    def removeListener(self, eventQueue):
        self.listeners.remove(eventQueue)

    async def cleanup(self):
        await gather(*[l.put(None) for l in self.listeners])

    async def registerHandler(self):
        # Subscribe to /org/mpris/MediaPlayer2/Metadata property changes,
        # which mean the song has changed
        rule = PropertiesChanged()
        rule.add_arg_condition(0, Player().interface, "string")

        session_bus = Proxy(DBus(), self.protocol)
        subscribed = await session_bus.AddMatch(rule) == ()
        if not subscribed:
            raise RuntimeError("Could not register matching rule")
        self.protocol.router.subscribe_signal(
            path="/org/mpris/MediaPlayer2",
            interface="org.freedesktop.DBus.Properties",
            member="PropertiesChanged",
            callback=partial(self.handlePlayerPropertiesChanged),
        )

    def handlePlayerPropertiesChanged(self, signalData):
        """
        Check if the current song's metadata property changed.
        Schedule a task in that case.
        """
        interface, changed, invalidated = signalData
        loop = get_event_loop()
        for name, variant in changed.items():
            if name == "Metadata":
                typename, value = variant
                loop.create_task(self.handleSongChanged(value))
                return

    async def handleSongChanged(self, metadata):
        track = parseTrackMetadata(metadata)
        # Network streams have unknown length until they start buffering
        # There might be multiple PropertiesChanged signal for the same
        # song, therefore a song only changes if the uri does not match with
        # the first song in the queue

        # Metadata's URI will be None if there is no more songs to play
        if not track.uri:
            self.queue = []
            return

        songChanged = len(self.queue) == 0 or not self.queue[0].matchesUrl(track.uri)
        if songChanged:
            print("Handle song changed: {}".format(metadata))
            # Remove all elements from queue until the current
            mismatchCurrent = lambda x: not x.matchesUrl(track.uri)

            it = dropwhile(mismatchCurrent, iter(self.queue))
            self.queue = list(it)

            # Notify clients of song changed event
            await gather(*self.notifyListChange())


class TrackEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Track):
            return {"id": obj.id, "title": obj.title, "caption": obj.caption}
        if isinstance(obj, QueueState):
            return {"etag": str(obj.etag), "tracks": obj.tracks}
        return super().default(obj)

