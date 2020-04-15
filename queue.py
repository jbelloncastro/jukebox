#!/usr/bin/python3

from jeepney.integrate.blocking import Proxy
from org_mpris_MediaPlayer2 import Player, TrackList
from properties import PlayerProperties, TrackListProperties
from search import YouTubeFinder

# Talk with DBus daemon itself
from jeepney.integrate.blocking import connect_and_authenticate

playlist = True

with connect_and_authenticate(bus="SESSION") as connection:
    finder = YouTubeFinder()
    result = finder.search("they are taking the hobbits to isenhart")

    if not playlist:
        player = Proxy(Player(), connection)
        reply = player.OpenUri(result.url)
    else:
        # Start playing this one
        setCurrent = False
        # Insert at the beginning of the list
        track = "/org/mpris/MediaPlayer2/TrackList/NoTrack"

        tracklist = Proxy(TrackList(), connection)
        reply = tracklist.AddTrack(result.url, track, setCurrent)
        print(reply)
