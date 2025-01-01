
import argparse
import asyncio
import signal
import sys

from .dbus.org_freedesktop_DBus import DBus
from .dbus.signals import NameOwnerChanged

from .server.server import Server
from .server.tracklist import Queue

from jeepney import DBusErrorResponse
from jeepney.io.asyncio import  open_dbus_router
from jeepney.io.asyncio import Proxy


async def main(address, port, bus_name):
    loop = asyncio.get_event_loop()

    # Create a future that is done when the user requests the service's termination
    stopRequested = loop.create_future()
    for s in {signal.SIGINT, signal.SIGTERM}:
        loop.add_signal_handler(s, lambda: stopRequested.set_result(None))

    async with open_dbus_router() as dbusRouter:
        # Pick first VLC instance we find
        dbusProxy = Proxy(DBus(), dbusRouter)

        # If no VLC is running, then the bus name will not have an owner.
        # In that case, we can wait for the name to be acquired.

        # When the bus name is not org.mpris.MediaPlayer2.vlc, waiting for activation is not likely going to work,
        # since the first name depends on the process PID and whether or not there are multiple instances active.
        rule = NameOwnerChanged()
        rule.add_arg_condition(0, bus_name)

        vlcInstances = []
        with dbusRouter.filter(rule) as queue:
            subscribed = await Proxy(DBus(), dbusRouter).AddMatch(rule.serialise()) == ()
            assert subscribed

            # Originally looked for all instances using 'ListQueuedOwners'.
            # However, vlc does not queue bus name reservation but instead creates unique bus names for each instance.
            # Therefore, we need to list all bus names and filter them by name.
            response, = await dbusProxy.ListNames()
            vlcInstances = list(instance for instance in response if instance.startswith(bus_name))

            if not vlcInstances:
                # Wait for first instance to start or for a stop request
                async def ownerChanged():
                    message = await queue.get()
                    name, oldOwner, newOwner = message.body
                    return newOwner

                changed = loop.create_task(ownerChanged())

                print(f"DBus bus name {bus_name} was not found. Waiting for activation.")
                await asyncio.wait([stopRequested, changed], return_when=asyncio.FIRST_COMPLETED)
                if changed.done():
                    vlcInstances = [changed.result()]

        if vlcInstances:
            tracklist = Queue(dbusRouter, vlcInstances[0])
            server = Server(address, port, tracklist)
            try:
                await tracklist.handlers # wait dbus signal subscription is completed
                await server.start()
                print("Running. Press Ctrl-C to exit.")
                await stopRequested
            finally:
                await server.stop()

        print("Exiting...")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="jukebox", description="Stream music from a web media service on demand")
    parser.add_argument("http_server_address", nargs="?", help="address and port pair to listen for HTTP connections (default: 'localhost:8080')", default="localhost:8080")
    parser.add_argument("-b", "--bus_name", help="media player bus name (default: 'org.mpris.MediaPlayer2.vlc')", default="org.mpris.MediaPlayer2.vlc")

    args = parser.parse_args()

    http_addr = re.fullmatch(r"([^:]+):([0-9]+)", args.http_server_address)
    if http_addr is None:
        print(f"Error: {parser.http_server_address} is not a valid host:port pair")
        args.print_help()
        sys.exit(1)

    host = http_addr.group(1)
    port = int(http_addr.group(2))
    print(f"Listening at: http://{host}:{port}")
    asyncio.run(main(host, port, args.bus_name))
