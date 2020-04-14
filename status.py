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

class TrackListListener:
    " Try to track when VLC bus is ready to use (has owner)"

    def handleSignal(self, data):
        "Callback for when we receive a NameOwnerChanged signal"

        metadata, afterTrack = data
        print("Track added after {}:\n{}".format(afterTrack, metadata))

    def __init__(self, connection):
        # Signal matching criteria
        rule = TrackListSignals().TrackAdded()

        # Register the callback
        connection.router.subscribe_signal(
            path=TrackList().object_path,
            interface=TrackList().interface,
            member="TrackAdded",
            callback=partial(self.handleSignal),
        )

        # Object to interact with D-Bus daemon
        session_bus = Proxy(message_bus, connection)

        # Register signals matching the specified criteria
        success = session_bus.AddMatch(rule) == ()
        if not success:
            raise RuntimeError("Could not register matching rule")

