
import asyncio
import signal

from .dbus.org_freedesktop_DBus import DBus
from .dbus.signals import NameOwnerChanged

from .server.server import Server
from .server.tracklist import Queue

from jeepney import DBusErrorResponse
from jeepney.io.asyncio import  open_dbus_router
from jeepney.io.asyncio import Proxy

async def main():
    address="0.0.0.0"
    port=8080
    loop = asyncio.get_event_loop()

    stopRequested = loop.create_future()
    for s in {signal.SIGINT, signal.SIGTERM}:
        loop.add_signal_handler(s, lambda: stopRequested.set_result(None))

    async with open_dbus_router() as dbusRouter:
        # Pick first VLC instance we see
        dbusProxy = Proxy(DBus(), dbusRouter)

        rule = NameOwnerChanged()
        rule.add_arg_condition(0, 'org.mpris.MediaPlayer2.vlc')

        with dbusRouter.filter(rule) as queue:
            subscribed = await Proxy(DBus(), dbusRouter).AddMatch(rule.serialise()) == ()
            assert subscribed
            try:
                response = await dbusProxy.ListQueuedOwners('org.mpris.MediaPlayer2.vlc')
                vlcInstances, = response.body
            except DBusErrorResponse as error:
                if error.name != 'org.freedesktop.DBus.Error.NameHasNoOwner':
                    raise error
                message = await queue.get()
                name, oldOwner, newOwner = message.body
                vlcInstances = [newOwner]

        tracklist = Queue(dbusRouter, vlcInstances[0])
        server = Server(address, str(port), tracklist)
        try:
            await tracklist.handlers # wait dbus signal subscription is completed
            await server.start()
            print("Running. Press Ctrl-C to exit.")
            await stopRequested
        finally:
            print("Exiting...")
            await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
