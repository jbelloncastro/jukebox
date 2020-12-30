import asyncio

from functools import partial

from itertools import dropwhile

from jeepney.io.asyncio import open_dbus_connection, DBusRouter, Proxy
from jeepney.bus_messages import MatchRule, DBus
from jeepney.wrappers import Properties

from jukebox.dbus.org_mpris_MediaPlayer2 import Player, TrackList
from jukebox.dbus.signals import PropertiesChanged, TrackAdded, TrackRemoved, TrackListReplaced
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
        self.playerTrackId = None

    def matchesUrl(self, url):
        return self.url == url


class QueueState:
    def __init__(self, queue):
        self.tracks = queue.tracks.copy()
        self.etag = str(queue.uuid.hex)


class Queue:
    def __init__(self, connection):
        self.uuid = uuid4()

        # List of tracks
        self.tracks = []
        # Clients subscribed to song change events
        self.listeners = set()
        # Event handlers
        self.tasks = []

        self.router = DBusRouter(connection)

    @classmethod
    async def create(cls):
        queue = Queue(await open_dbus_connection())
        await queue.registerHandler()
        return queue

    async def notifyListChange(self, message = None):
        # Regenerate etag
        self.uuid = uuid4()

        # Send request to change the tracklist
        if message:
            await message

        # Read tracklist again to match player's track id with our tracklist
        properties = Proxy(Properties(TrackList()), self.router)
        tracks = await properties.get("Tracks")
        print("Tracklist has changed: {}".format(repr(tracks)))

        # Notify subscribers with new tracklist
        state = QueueState(self)
        await asyncio.gather(*[client.put(state) for client in self.listeners])

    async def addTrack(self, track):
        trackIdTail = "/org/mpris/MediaPlayer2/TrackList/Append"

        # Resume playing if necessary
        properties = Proxy(Properties(Player()), self.router)
        status = await properties.get("PlaybackStatus")
        resume = status[0] == ("s", "Stopped")

        self.tracks.append(track)

        tracklist = Proxy(TrackList(), self.router)
        message = tracklist.AddTrack(track.url, trackIdTail, resume)
        await self.notifyListChange(message)
        return self.tracks

    async def removeTrack(self, track_id):
        print("Remove track: {}".format(track_id))
        player = Proxy(Player(), self.router)
        if track_id == 0 and len(self.tracks) > 0:
            self.tracks = self.tracks[1:]

            message = player.Next()
            await self.notifyListChange(message)
        # if track_id < len(self.tracks):
        #     del self.tracks[track_id]
        #     # TODO: We must update the tracklist in the media player too!
        #     await asyncio.gather(*self.notifyListChange())
        else:
            raise ValueError()

    async def removeTrack(self, track_id):
        print("Remove track: {}".format(track_id))
        if track_id == 0 and len(self.queue) > 0:
            self.queue = self.queue[1:]
            nextTrack = Player().Next()
            sequence = self.notifyListChange()
            sequence.append(self.protocol.send_message(nextTrack))
            await gather(*sequence)
        # if track_id < len(self.queue):
        #     del self.queue[track_id]
        #     # TODO: We must update the tracklist in the media player too!
        #     await gather(*self.notifyListChange())
        else:
            raise ValueError()

    def addListener(self, eventQueue):
        self.listeners.add(eventQueue)

    def removeListener(self, eventQueue):
        self.listeners.remove(eventQueue)

    async def cleanup(self):
        self.listeners.extend(l.put(None) for l in self.listeners)
        await asyncio.gather(*self.listeners)
        self.listeners = []

    async def registerHandler(self):
        async def handleEvent(rule, callback):
            subscribed = await Proxy(DBus(), self.router).AddMatch(rule) == ()
            if not subscribed:
                raise RuntimeError("Could not register matching rule")

            with self.router.filter(rule) as eventQueue:
                callback(await eventQueue.get())

        # Subscribe to /org/mpris/MediaPlayer2/Metadata property changes,
        # which mean the song has changed
        rule = PropertiesChanged()
        rule.add_arg_condition(0, Player().interface, "string")
        task = asyncio.create_task(handleEvent(rule, self.handlePlayerPropertiesChanged))
        self.tasks.append(task)

        # Subscribe to TrackListReplaced signal
        # which mean a song was added or removed
        rule = TrackAdded()
        rule.add_arg_condition(0, Player().interface, "string")
        task = asyncio.create_task(handleEvent(rule, lambda: print("TrackListReplaced signal")))
        self.tasks.append(task)

        # Print a message whenever an unhandled signal arrives
        rule = MatchRule(path=Player().object_path, type="signal")
        task = asyncio.create_task(handleEvent(rule, lambda msg: print("Signal unhandled")))
        self.tasks.append(task)

    def handlePlayerPropertiesChanged(self, signalData):
        """
        Check if the current song's metadata property changed.
        Schedule a task in that case.
        """
        interface, changed, invalidated = signalData
        for name, variant in changed.items():
            if name == "Metadata":
                typename, value = variant
                asyncio.create_task(self.handleSongChanged(value))
                return

    async def handleSongChanged(self, metadata):
        track = parseTrackMetadata(metadata)
        # Network streams have unknown length until they start buffering
        # There might be multiple PropertiesChanged signal for the same
        # song, therefore a song only changes if the uri does not match with
        # the first song in the queue

        # Metadata's URI will be None if there is no more songs to play
        if not track.uri:
            self.tracks = []
            return

        songChanged = len(self.tracks) == 0 or not self.tracks[0].matchesUrl(track.uri)
        if songChanged:
            print("Handle song changed: {}".format(metadata))
            # Remove all elements from queue until the current
            mismatchCurrent = lambda x: not x.matchesUrl(track.uri)

            it = dropwhile(mismatchCurrent, iter(self.tracks))
            self.tracks = list(it)

            # Notify clients of song changed event
            await self.notifyListChange()


class TrackEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Track):
            return {"id": obj.id, "title": obj.title, "caption": obj.caption}
        if isinstance(obj, QueueState):
            return {"etag": str(obj.etag), "tracks": obj.tracks}
        return super().default(obj)

