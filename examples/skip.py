#!/usr/bin/python3
from jeepney.integrate.blocking import connect_and_authenticate, Proxy

from jukebox.mpris import Player

with connect_and_authenticate(bus="SESSION") as connection:
    player = Proxy(Player(), connection)
    player.Next()

