
import asyncio
import signal

from .dbus.org_freedesktop_DBus import DBus

from .server.server import Server
from .server.tracklist import Queue

from jeepney.io.asyncio import Proxy
from jeepney.io.asyncio import  open_dbus_router

async def main():
    address="0.0.0.0"
    port=8080
    loop = asyncio.get_event_loop()

    stopRequested = loop.create_future()
    for s in {signal.SIGINT, signal.SIGTERM}:
        loop.add_signal_handler(s, lambda: stopRequested.set_result(None))

    async with open_dbus_router() as dbusRouter:
        # Pick first VLC instance we see
        response = await Proxy(DBus(), dbusRouter).ListQueuedOwners('org.mpris.MediaPlayer2.vlc')
        vlcInstances = response[0]
        if not vlcInstances:
            raise RuntimeError("VLC is not running")

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
