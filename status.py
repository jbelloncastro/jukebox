from functools import partial

from jeepney import DBusAddress
from jeepney.bus_messages import MatchRule, message_bus
from jeepney.integrate.blocking import Proxy

from org_mpris_MediaPlayer2 import Player, TrackList


class MatchSignal(MatchRule):
    "Matching rule for bus owner change signals"

    def __init__(self, address, name):
        super().__init__(
            type="signal",
            sender=address.bus_name,
            interface=address.interface,
            path=address.object_path,
            member=name,
        )


class DBusSignals:
    def NameOwnerChanged(self):
        return MatchSignal(message_bus, "NameOwnerChanged")

class TrackListSignals:
    def TrackListReplaced(self):
        return MatchSignal(TrackList(), "TrackListReplaced")

    def TrackAdded(self):
        return MatchSignal(TrackList(), "TrackAdded")

    def TrackRemoved(self):
        return MatchSignal(TrackList(), "TrackRemoved")

    def TrackMetadataChanged(self):
        return MatchSignal(TrackList(), "TrackMetadataChanged")


class PlayerListener:
    " Try to track when VLC bus is ready to use (has owner)"

    def handleSignal(self, data):
        "Callback for when we receive a NameOwnerChanged signal"

        name, old_owner, new_owner = data
        print(
            'Name {} owner changed from "{}" to "{}"'.format(name, old_owner, new_owner)
        )

    def __init__(self, connection):
        # Signal matching criteria
        rule = DBusSignals().NameOwnerChanged()
        # Match only if sender is the media player
        rule.add_arg_condition(0, Player().bus_name, "string")

        # Register the callback
        connection.router.subscribe_signal(
            path=rule.conditions["path"],
            interface=rule.conditions["interface"],
            member=rule.conditions["member"],
            callback=partial(self.handleSignal),
        )

        # Object to interact with D-Bus daemon
        session_bus = Proxy(message_bus, connection)

        # Register signals matching the specified criteria
        success = session_bus.AddMatch(rule) == ()
        if not success:
            raise RuntimeError("Could not register matching rule")

class PlayStatusListener:
    " Try to track when VLC changes song, starts and stops playing"
    def handlePlayStateChange(self, data):
        pass

    def handleCurrentTrack(self, data):
        pass

    def handleTrackListChange(self, data):
        "Callback for when we receive a NameOwnerChanged signal"
        invalidated = data[2]
        if 'Tracks' in invalidated:
            print("Track list changed\n")
            tracklist_bus = Proxy(TrackListProperties(), self.connection)
            print(tracklist_bus.Tracks())

    def handleSignal(self, data):
        interface, changed, invalidated = data
        print('Interface: {}, Changed: {}, Invalidated: {}'.format(interface, changed, invalidated))

    def __init__(self, connection):
        self.connection = connection
        # Object to interact with D-Bus daemon
        session_bus = Proxy(message_bus, connection)

        # Register signals matching the specified criteria
        rule = MatchRule(type='signal',
                sender='org.mpris.MediaPlayer2.vlc',
                interface='org.freedesktop.DBus.Properties',
                path='/org/mpris/MediaPlayer2',
                member='PropertiesChanged',
                )

        # Match only properties in Player and TrackList interfaces
        # rule.add_arg_condition(0, Player().interface, "string")
        # rule.add_arg_condition(0, TrackList().interface, "string")

        success = session_bus.AddMatch(rule) == ()
        if not success:
            raise RuntimeError("Could not register matching rule")

        # Register callback for tracklist changes
        connection.router.subscribe_signal(
            path='/org/mpris/MediaPlayer2',
            interface='org.freedesktop.DBus.Properties',
            member="PropertiesChanged",
            callback=partial(self.handleSignal),
        )

