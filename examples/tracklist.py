#!/usr/bin/python3

from jeepney.integrate.blocking import Proxy
from jukebox.dbus.org_mpris_MediaPlayer2 import Player, TrackList
from jukebox.dbus.properties import PlayerProperties, TrackListProperties
from jukebox.server.search import YouTubeFinder
from jukebox.server.status import PlayerListener, PlayStatusListener, TrackListListener

# Talk with DBus daemon itself
from jeepney.integrate.blocking import connect_and_authenticate

try:
    with connect_and_authenticate(bus="SESSION") as connection:
        tracklistProperties = Proxy(TrackListProperties(), connection)
        tracks = tracklistProperties.Tracks()[0]
        print(tracks)

        # matcher = PlayerListener(connection)
        matcher = PlayStatusListener(connection)
        # matcher = TrackListListener(connection)
        while True:
            connection.recv_messages()
except KeyboardInterrupt:
    pass
