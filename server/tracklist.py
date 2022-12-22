import asyncio

from collections import deque
from contextlib import asynccontextmanager
from functools import partial
from itertools import dropwhile

from jeepney.io.asyncio import Proxy
from jeepney.bus_messages import MatchRule, DBus, Message, MessageType, HeaderFields
from jeepney.wrappers import Properties, MessageGenerator

from jukebox.dbus.org_mpris_MediaPlayer2 import Player, TrackList
from jukebox.dbus.signals import PropertiesChanged, TrackAdded, TrackRemoved, TrackListReplaced, Seeked
from jukebox.server.track_metadata import TrackMetadata

from json import JSONEncoder

from uuid import uuid4

def zip_equal(iterable1, iterable2):
    """
    Example logic:
    a = range(3)
    b = range(1, 5)
    zip_equal(a, b)
    > (0, None)
    > (1, 1)
    > (2, 2)
    > (None, 3)
    > (None, 4)
    """
    it1 = iter(iterable1)
    it2 = iter(iterable2)
    a, b = (None, None)
    try:
        a = next(it1)
        b = next(it2)
        while True:
            if a != b:
                yield(a, None)
                a = next(it1)
            else:
                yield (a, b)
                a = next(it1)
                b = next(it2)
    except StopIteration:
        pass
    finally:
        del it1
    # it1 is exhausted
    try:
        if a != b:
                yield (None, b)
        for b in it2:
                yield (None, b)
    finally:
        del it2


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
        self.tracks = list(queue.tracklist)
        self.etag = str(queue.uuid.hex)


class Queue:
    def __init__(self, router, busName):
        self.uuid = uuid4()

        assert isinstance(busName, str)
        self.bus = busName
        self.router = router

        # Map of tracks by player trackid
        self.tracks = {}
        # List of tracks in media player
        self.tracklist = []
        self.playing = -1
        # List of tracks pending to add to queue
        self.pending = deque()

        # Clients subscribed to song change events
        self.listeners = set()
        # Event handlers
        self.handlers = asyncio.create_task(self.registerHandler())

    def instanceProxy(self, generator :MessageGenerator):
        """
        Returns a Proxy instance pointing to VLC instance's bus name and using
        the object's router
        """
        generator.bus_name = self.bus
        return Proxy(generator, self.router)

    async def notifyListChange(self):
        # Read tracklist again to match player's track id with our tracklist
        properties = self.instanceProxy(Properties(TrackList()))
        response = await properties.get("Tracks")
        signature, tracks = response[0]
        print("Tracklist is now: {}".format(repr(tracks)))

        # Notify subscribers with new tracklist
        state = QueueState(self)
        await asyncio.gather(*[client.put(state) for client in self.listeners])

    async def addTrack(self, track):
        trackIdTail = "/org/mpris/MediaPlayer2/TrackList/Append"

        # Resume playing if necessary
        properties = self.instanceProxy(Properties(Player()))
        response = await properties.get("PlaybackStatus")

        signature, status = response[0]
        resume = (signature, status) == ("s", "Stopped")

        self.tracklist.append(track)

        # Regenerate etag
        self.uuid = uuid4()

        tracklist = self.instanceProxy(TrackList())
        await tracklist.AddTrack(track.url, trackIdTail, resume)

        await self.notifyListChange()

    async def removeTrack(self, index):
        print("Remove track: {}".format(track_id))
        if index == 0 and len(self.tracklist) > 0:
            # Regenerate etag
            self.uuid = uuid4()

            self.trackslist = self.tracks[1:]

            player = self.instanceProxy(Player())
            await player.Next()

            await self.notifyListChange()
        else:
            raise ValueError()

    @asynccontextmanager
    async def createListener(self):
        eventQueue = asyncio.Queue()
        self.listeners.add(eventQueue)
        try:
            yield eventQueue
        finally:
            self.listeners.remove(eventQueue)

    async def cleanup(self):
        self.handlers.cancel("Cleanup")
        await asyncio.gather(*[t for queue in self.listeners
                                    for t in [queue.put(None), queue.join()]])
        self.tasks = []
        self.listeners = set()

    async def registerHandler(self):
        async def eventHandler(rule, subscribedFuture, callback):
            with self.router.filter(rule, bufsize=10) as handler:
                # We need to send this to the session dbus
                subscribed = await Proxy(DBus(), self.router).AddMatch(rule) == ()
                if subscribed:
                    subscribedFuture.set_result(True)
                else:
                    subscribedFuture.set_exception(
                            RuntimeError("Could not register matching rule"))
                while True:
                    value = await handler.get()
                    callback(value)

        def handleEvent(rule, callback):
            loop = asyncio.get_running_loop()
            subscribed = loop.create_future()
            loop.create_task(eventHandler(rule, subscribed, callback))
            return subscribed

        allSubscribed = []
        # Subscribe to /org/mpris/MediaPlayer2/Metadata property changes,
        # which mean the song has changed
        rule = PropertiesChanged(sender=self.bus)
        # rule.add_arg_condition(0, Player().interface, "string")
        allSubscribed.append(
                handleEvent(rule, self.handlePlayerPropertiesChanged))

        # Subscribe to TrackListReplaced signal
        # which mean a song was added or removed
        # rule = TrackAdded()
        # rule.add_arg_condition(0, Player().interface, "string")
        # handlers.create_task(handleEvent(rule, lambda: print("TrackListReplaced signal")))
        # self.tasks.append(task)

        # Subscribe to /org/mpris/MediaPlayer2/TrackList property changes,
        # which mean song were added or removed
        # rule = PropertiesChanged()
        # rule.add_arg_condition(0, TrackList().interface, "string")
        # handlers.create_task(handleEvent(rule, self.notifyListChange))
        # self.tasks.append(task)

        # Ignore MediaPlayer2.Player.Seeked signal
        # rule = Seeked()
        # rule.add_arg_condition(0, Player().interface, "string")
        # handlers.create_task(handleEvent(rule, lambda: None))
        # self.tasks.append(task)
        await asyncio.gather(*allSubscribed)
        print("DBus signals subscribed")

    def handlePlayerPropertiesChanged(self, signalMessage):
        """
        Check if the current song's metadata property changed.
        Schedule a task in that case.
        """
        print(f"Handle player properties changed\n{signalMessage}")
        assert signalMessage.header.message_type == MessageType.signal
        assert signalMessage.header.fields[HeaderFields.interface] == 'org.freedesktop.DBus.Properties'
        assert signalMessage.header.fields[HeaderFields.path] == '/org/mpris/MediaPlayer2'
        assert signalMessage.header.fields[HeaderFields.signature] == 'sa{sv}as'

        interface, changed, invalidated = signalMessage.body
        for name, variant in changed.items():
            if name == "Metadata":
                typename, value = variant
                asyncio.create_task(self.handleSongChanged(value))
                return

    async def handleSongChanged(self, metadata):
        track = TrackMetadata.fromMPRISMetadata(metadata)
        print(f"handleSongChanged\n{track}")
        # Network streams have unknown length until they start buffering
        # There might be multiple PropertiesChanged signal for the same
        # song, therefore a song only changes if the uri does not match with
        # the first song in the queue

        # Metadata's URI will be None if there is no more songs to play
        if not track.uri:
            self.tracklist = []
            self.tracks = {}
            self.pending = deque()
            return

        songChanged = len(self.tracklist) == 0 or not self.tracklist[0].matchesUrl(track.uri)
        if songChanged:
            print("Handle song changed: {}".format(track))
            # Remove all elements from queue until the current
            mismatchCurrent = lambda t: not t.matchesUrl(track.uri)

            self.tracklist = list(dropwhile(mismatchCurrent, self.tracklist))

            # Notify clients of song changed event
            await self.notifyListChange()


class TrackEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Track):
            return {"id": obj.id, "title": obj.title, "caption": obj.caption}
        if isinstance(obj, QueueState):
            return {"etag": str(obj.etag), "tracks": obj.tracks}
        return super().default(obj)

