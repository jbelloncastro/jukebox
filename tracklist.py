
from jeepney import DBusAddress, Properties
from org_mpris_MediaPlayer2 import TrackList

def getTracks():
    return Properties(TrackList()).get('Tracks')
