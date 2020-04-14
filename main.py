#!/usr/bin/python3

from org_mpris_MediaPlayer2 import Player, TrackList
from properties import PlayerProperties, TrackListProperties
from search import YouTubeFinder
from status import PlayerStatusTracker

# Talk with DBus daemon itself
from jeepney.integrate.blocking import connect_and_authenticate

trackStatus = False
findVideo = False
playlist = True

try:
    with connect_and_authenticate(bus="SESSION") as connection:
        if trackStatus:
            matcher = PlayerStatusTracker(connection)
            while True:
                connection.recv_messages()
        elif findVideo:
            finder = YouTubeFinder()
            result = finder.search("they are taking the hobbits to isenhart")

            if not playlist:
                method = Player().OpenUri(result.url)
                reply = connection.send_and_get_reply(method)
            else:
                # Start playing this one
                setCurrent = True
                # Insert at the beginning of the list
                track = "/org/mpris/MediaPlayer2/TrackList/NoTrack"

                method = TrackList().AddTrack(result.url, track, setCurrent)
                reply = connection.send_and_get_reply(method)
        elif playlist:
            l = connection.send_and_get_reply(TrackListProperties().Tracks())[0]
            print(l)
except KeyboardInterrupt:
    pass
