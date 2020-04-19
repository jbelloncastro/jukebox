#!/usr/bin/python3

from jeepney.integrate.blocking import Proxy
from org_mpris_MediaPlayer2 import Player, TrackList
from properties import PlayerProperties, TrackListProperties
from search import YouTubeFinder

# Talk with DBus daemon itself
from jeepney.integrate.blocking import connect_and_authenticate

import hashlib

playlist = True
list_hash = hashlib.sha1()

with connect_and_authenticate(bus="SESSION") as connection:
    finder = YouTubeFinder()
    tracklist = Proxy(TrackList(), connection)
    player = Proxy(Player(), connection)
    playerProperties = Proxy(PlayerProperties(), connection)

    try:
        while True:
            query = input("ytsearch: ")
            if len(query) > 0:
                result = finder.search(query)
                url = result.url
                list_hash.update(str.encode(result.id))
                print("Playing url: {}, digest: {}".format(url, list_hash.hexdigest()))

                # Insert at the beginning of the list
                track = "/org/mpris/MediaPlayer2/TrackList/Append"
                # track = "/org/mpris/MediaPlayer2/TrackList/NoTrack"
                # Insert after element
                # track = "/org/videolan/vlc/playlist/0"
                # track = ""

                # Resume playing if necessary
                # Alternative: player.GoTo('/org/videolan/vlc/playlist/{id}')
                status = playerProperties.PlaybackStatus()[0]
                resume = status == ("s", "Stopped")
                print("Status: {}, Resume: {}".format(status, resume))
                reply = tracklist.AddTrack(url, track, resume)
                if resume:
                    player.Play()
    except EOFError:
        pass
    except KeyboardInterrupt:
        pass
