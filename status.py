from jeepney import DBusAddress

from jeepney.bus_messages import MatchRule, message_bus
from jeepney.integrate.blocking import Proxy

from functools import partial

from org_mpris_MediaPlayer2 import Player


class MatchNameOwnerChanged(MatchRule):
    "Matching rule for bus owner change signals"

    def __init__(self):
        super().__init__(
            type="signal",
            sender=message_bus.bus_name,
            interface=message_bus.interface,
            path=message_bus.object_path,
            member="NameOwnerChanged",
        )


class PlayerStatusTracker:
    " Try to track when VLC bus is ready to use (has owner)"

    def handleSignal(self, data):
        "Callback for when we receive a NameOwnerChanged signal"

        name, old_owner, new_owner = data
        if name == Player().bus_name:
            print(
                'Name {} owner changed from "{}" to "{}"'.format(
                    name, old_owner, new_owner
                )
            )

    def __init__(self, connection):
        # This defines messages for talking to the D-Bus bus daemon itself:
        session_bus = Proxy(message_bus, connection)

        # Tell the session bus to pass us matching signal messages:
        success = session_bus.AddMatch(MatchNameOwnerChanged()) == ()
        if not success:
            raise RuntimeError("Could not create matching rule")

        # Bind self and member function
        callback = partial(self.ownerChanged)

        # Connect the callback to the relevant signal
        connection.router.subscribe_signal(
            path=message_bus.object_path,
            interface=message_bus.interface,
            member="NameOwnerChanged",
            callback=callback,
        )
