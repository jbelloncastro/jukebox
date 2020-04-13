
from jeepney import DBusAddress

from jeepney.bus_messages import MatchRule, message_bus
from jeepney.integrate.blocking import Proxy

from functools import partial

from org_mpris_MediaPlayer2 import Player

class PlayerStatusTracker:
    " Try to track when VLC bus is ready to use (has owner)"
    # DBus daemon bus adddress and interface
    address = DBusAddress('/org/freedesktop/DBus',
                          bus_name='org.freedesktop.DBus',
                          interface='org.freedesktop.DBus')

    # Matching rule for bus owner change signals
    match = MatchRule(type="signal",
                      sender=address.bus_name,
                      interface=address.interface,
                      member="NameOwnerChanged",
                      path=address.object_path)

    def ownerChanged(self, data):
        "Callback for when we receive a NameOwnerChanged signal"

        name, old_owner, new_owner = data
        if name == Player().bus_name:
            print('Name {} owner changed from "{}" to "{}"'.format(
                name, old_owner, new_owner))

    def __init__(self, connection):
        # This defines messages for talking to the D-Bus bus daemon itself:
        session_bus = Proxy(message_bus, connection)

        # Tell the session bus to pass us matching signal messages:
        success = session_bus.AddMatch(PlayerStatusTracker.match) == ()
        if not success:
            raise RuntimeError("Could not create matching rule")

        # Connect the callback to the relevant signal
        connection.router.subscribe_signal(path=PlayerStatusTracker.address.object_path,
                                           interface=PlayerStatusTracker.address.interface,
                                           member="NameOwnerChanged",
                                           callback=partial(self.ownerChanged))
