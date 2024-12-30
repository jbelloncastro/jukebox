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
        self.tracklist_id = None

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
        self.tracklist_lock = asyncio.Lock()
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

    async def notifyListChange(self, state :QueueState):
        # Notify subscribers with new tracklist
        print("Put in listeners: {}".format([t.title for t in self.tracklist]))
        await asyncio.gather(*[client.put(state) for client in self.listeners])

    async def addTrack(self, track):
        async with self.tracklist_lock:
            # Regenerate etag
            self.uuid = uuid4()
            self.tracklist.append(track)

            # Check if player is stopped. Resume playing if necessary
            properties = self.instanceProxy(Properties(Player()))
            response = await properties.get("PlaybackStatus")
            signature, status = response[0]

            tracklist = self.instanceProxy(TrackList())
            trackIdTail = "/org/mpris/MediaPlayer2/TrackList/Append"
            resume = (signature, status) == ("s", "Stopped")
            await tracklist.AddTrack(track.url, trackIdTail, resume)

            # Read tracklist again to match player's track id with our tracklist
            # TODO: would be a good idea to wait for PropertiesChanged signal.
            # Must make sure we guarantee the order of track additions such
            # that appending two tracks concurrently returns the right result.
            properties = self.instanceProxy(Properties(TrackList()))
            response = await properties.get("Tracks")
            signature, tracks = response[0]
            print("Tracklist is now: {}".format(repr(tracks)))

            track.tracklist_id = tracks[-1]
            state = QueueState(self)
        print("Send notification change!")
        await self.notifyListChange(state)

    async def removeTrack(self, index):
        print("Remove track: {}".format(index))
        if index == 0 and len(self.tracklist) > 0:
            async with self.tracklist_lock:
                # Regenerate etag
                self.uuid = uuid4()

                self.trackslist = self.tracks[1:]

                player = self.instanceProxy(Player())
                await player.Next()

                state = QueueState(self)
            await self.notifyListChange(state)
        else:
            raise ValueError("Can only remove the first track in the list")

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
        # We expect the properties to always be located in 'changed' map,
        # not in the 'invalidated' list.
        assert all(i not in invalidated for i in ['PlaybackStatus', 'Metadata', 'CanGoNext'])

        if (variant := changed.get("PlaybackStatus",None)) is not None \
           and variant == ('s', 'Stopped'):
            # Player stopped after reaching the end of the tracklist or was told to do so.
            # There should not be a new song to play, but VLC player still forwards all state (including current song) even if unchanged.

            # assert "Metadata" not in changed

            asyncio.create_task(self.handleSongChanged(None))
        elif (variant := changed.get("Metadata", None)) is not None:
            # A song has changed
            typename, value = variant
            asyncio.create_task(self.handleSongChanged(value))

        if (variant := changed.get("CanGoNext", None)) is not None \
           and variant == ('b', False):
            # We are now playing the last song in the queue
            # This does not trigger if this is the first song being played
            pass


    async def handleSongChanged(self, metadata):
        # Network streams have unknown length until they start buffering
        # There might be multiple PropertiesChanged signal for the same
        # song, therefore a song only changes if the uri does not match with
        # the first song in the queue

        state = None
        async with self.tracklist_lock:
            # Metadata is None when there isn't any more songs to play
            if not metadata:
                self.tracklist = []
                self.tracks = {}
                self.pending = deque()
                state = QueueState(self)
            else:
                track = TrackMetadata.fromMPRISMetadata(metadata)
                songChanged = not self.tracklist or self.tracklist[0].tracklist_id != track.tracklist_id
                if songChanged:
                    print("Handle song changed. Current: {}; List: {}".format(
                                    track.tracklist_id,
                                    [t.tracklist_id for t in self.tracklist]))
                    # Remove all elements from queue until the current
                    mismatchCurrent = lambda t: t.tracklist_id != track.tracklist_id

                    self.tracklist = list(dropwhile(mismatchCurrent, self.tracklist))
                    state = QueueState(self)

        if state:
            # Notify clients of song changed event
            await self.notifyListChange(state)


class TrackEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Track):
            return {"id": obj.id, "title": obj.title, "caption": obj.caption}
        if isinstance(obj, QueueState):
            return {"etag": str(obj.etag), "tracks": obj.tracks}
        return super().default(obj)

