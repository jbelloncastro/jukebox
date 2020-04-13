# Jukebox
Play music via YouTube or other media service on demand.

Python server with HTTP frontend that uses DBus to control VLC media player.

## Dependencies
- jeepney: Python library to interact with the DBus daemon
- youtube-dl: searches and downloads videos from a number of media services

## Jeepney bindings generator for org.mpris.MediaPlayer2 interface
Generate bindings for vlc interface:
```
python3 -m jeepney.bindgen --name org.mpris.MediaPlayer2.vlc --path /org/mpris/MediaPlayer2
```
