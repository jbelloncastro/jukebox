# Jukebox
Play music via YouTube or other media service on demand.

Python application that provides a music queueing service with HTTP frontend. It uses DBus to control a media player running locally.

## Quickstart

1. Download project

       git clone https://github.com/jbelloncastro/jukebox.git jukebox/

3. Install dependencies, preferably in a virtual env.

       python3 -m venv .venv
       source .venv/bin/activate
       pip install -r requirements

4. Run applications.
    1. Media player. If running VLC you can also stream the audio to multiple devices over LAN. Remember that RTP uses
       multicast IP address domain, which for IPv4 ranges from 239.0.0.0 to 239.255.255.255 for local services.

           vlc --sout='#gather:transcode{vcodec=none,scodec=none,acodec=vorbis}:http{mux=ogg,dst=:8081/}' --no-sout-all --sout-keep
           vlc --sout='#transcode{vcodec=none,acodec=mpga}:rtp{mux=ts,dst=239.255.1.2,sdp=sap,name="TestStream"}' --no-sout-all --sout-keep

    2. Start server. By default, the server listens to HTTP connections in localhost:8080

           python -m jukebox

4. Access interface via a web browser. Put your search terms in the form and hit the submit button to queue a song.

## About DBUS and the MPRIS interface

This project communicates with media players using DBus Media Player Remote Interfacing Specification. To read more
about MPRIS, see https://specifications.freedesktop.org/mpris-spec/latest/

## Dependencies

- jeepney: provides an abstraction layer for communications using DBus protocol
- yt-dlp:  search videos from a number of media services
- aiohttp: asynchronously handle multiple HTTP client connections and DBus communication
- jinja2:  create html response document from the server playlist status

## Jeepney bindings generator for org.mpris.MediaPlayer2 interface
We can generate skeleton MPRIS interface objects with jeepney more or less automatically, using the following command. Note that this requires VLC to be running.
The generated files have been placed in `dbus/` directory and required manual changes for correct operation.

    python3 -m jeepney.bindgen --name org.mpris.MediaPlayer2.vlc --path /org/mpris/MediaPlayer2
