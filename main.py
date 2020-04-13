#!/usr/bin/python3

from search import YouTubeFinder
from org_mpris_MediaPlayer2 import Player, TrackList
from status import PlayerStatusTracker
from tracklist import getTracks

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
                setCurrent = True  # Start playing this one
                track = '/org/mpris/MediaPlayer2/TrackList/NoTrack'
                method = TrackList().AddTrack(result.url, track, setCurrent)

                reply = connection.send_and_get_reply(method)
        elif playlist:
            method = getTracks()
            l = connection.send_and_get_reply(method)[0]
            print(l)

except KeyboardInterrupt:
    pass
