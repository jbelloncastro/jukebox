from functools import partial

from jeepney import DBusAddress
from jeepney.bus_messages import MatchRule, message_bus
from jeepney.integrate.blocking import Proxy

from jukebox.dbus.org_mpris_MediaPlayer2 import Player, TrackList
from jukebox.signals import PropertiesChanged, TrackAdded
from jukebox.properties import TrackListProperties
from jukebox.server.track_metadata import parseTrackMetadata


class PlayStatusListener:
    " Try to track when VLC changes song, starts and stops playing"

    def handlePlayStateChange(self, data):
        pass

    def handleCurrentTrack(self, data):
        pass

    def handleTrackListChange(self, data):
        "Callback for when we receive a NameOwnerChanged signal"
        invalidated = data[2]
        if "Tracks" in invalidated:
            print("Track list changed\n")
            tracklist_bus = Proxy(TrackListProperties(), self.connection)
            tracks = tracklist_bus.Tracks()
            for track in tracklist_bus.GetTracksMetadata(tracks):
                print(parseTrackMetadata(track))

    def handleSignal(self, data):
        interface, changed, invalidated = data
        print(
            "Interface: {}, Changed: {}, Invalidated: {}".format(
                interface, changed, invalidated
            )
        )
        if "Tracks" in invalidated:
            tracklist_bus = Proxy(TrackList(), self.connection)
            tracks = tracklist_bus.GetTracksMetadata(
                ["/org/videolan/vlc/playlist/10", "/org/videolan/vlc/playlist/9"]
            )
            metadata = []
            for track in tracks[0]:
                t = parseTrackMetadata(track)
                print(repr(t))
                metadata.append(t)

    def __init__(self, connection):
        self.connection = connection
        # Object to interact with D-Bus daemon
        session_bus = Proxy(message_bus, connection)

        # Register signals matching the specified criteria
        rule = PropertiesChanged()

        # Match only properties in Player and TrackList interfaces
        # rule.add_arg_condition(0, Player().interface, "string")
        # rule.add_arg_condition(0, TrackList().interface, "string")

        success = session_bus.AddMatch(rule) == ()
        if not success:
            raise RuntimeError("Could not register matching rule")

        # Register callback for tracklist changes
        connection.router.subscribe_signal(
            path="/org/mpris/MediaPlayer2",
            interface="org.freedesktop.DBus.Properties",
            member="PropertiesChanged",
            callback=partial(self.handleSignal),
        )


class TrackListListener:
    def handleTrackListChange(self, data):
        "Callback for when we receive a TrackAdded signal"
        metadata, _ = data
        print("Added new track: {}".format(metadata))

    def __init__(self, connection):
        self.connection = connection
        # Object to interact with D-Bus daemon
        session_bus = Proxy(message_bus, connection)

        # Register signals matching the specified criteria
        rule = TrackAdded()

        success = session_bus.AddMatch(rule) == ()
        if not success:
            raise RuntimeError("Could not register matching rule")

        # Register callback for tracklist changes
        connection.router.subscribe_signal(
            path="/org/mpris/MediaPlayer2",
            interface="org.freedesktop.DBus.Properties",
            member="PropertiesChanged",
            callback=partial(self.handleTrackListChange),
        )
