from jeepney import DBusAddress
from jeepney.bus_messages import MatchRule


class PropertiesChanged(MatchRule):
    interface = "org.freedesktop.DBus.Properties"

    def __init__(
        self,
        object_path="/org/mpris/MediaPlayer2",
        bus_name="org.mpris.MediaPlayer2.vlc",
    ):
        super().__init__(
            type="signal",
            sender="org.mpris.MediaPlayer2.vlc",
            interface=PropertiesChanged.interface,
            path=object_path,
            member="PropertiesChanged",
        )


class TrackListReplaced(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"

    def __init__(
        self,
        object_path="/org/mpris/MediaPlayer2",
        bus_name="org.mpris.MediaPlayer2.vlc",
    ):
        super().__init__(
            type="signal",
            sender="org.mpris.MediaPlayer2.vlc",
            interface=PropertiesChanged.interface,
            path=object_path,
            member="TrackListReplaced",
        )


class TrackAdded(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"

    def __init__(
        self,
        object_path='/org/mpris/MediaPlayer2',
        bus_name="org.mpris.MediaPlayer2.vlc",
    ):
        super().__init__(
            type="signal",
            sender="org.mpris.MediaPlayer2.vlc",
            interface=PropertiesChanged.interface,
            path=object_path,
            member="TrackAdded",
        )


class TrackRemoved(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"

    def __init__(
        self,
        object_path="/org/mpris/MediaPlayer2",
        bus_name="org.mpris.MediaPlayer2.vlc",
    ):
        super().__init__(
            type="signal",
            sender="org.mpris.MediaPlayer2.vlc",
            interface=PropertiesChanged.interface,
            path=object_path,
            member="TrackRemoved",
        )


class TrackMetadataChanged(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"

    def __init__(
        self,
        object_path="/org/mpris/MediaPlayer2",
        bus_name="org.mpris.MediaPlayer2.vlc",
    ):
        super().__init__(
            type="signal",
            sender="org.mpris.MediaPlayer2.vlc",
            interface=PropertiesChanged.interface,
            path=object_path,
            member="TrackMetadataChanged",
        )


class Seeked(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"

    def __init__(
        self,
        object_path="/org/mpris/MediaPlayer2",
        bus_name="org.mpris.MediaPlayer2.vlc",
    ):
        super().__init__(
            type="signal",
            sender="org.mpris.MediaPlayer2.vlc",
            interface=PropertiesChanged.interface,
            path=object_path,
            member="Seeked",
        )
