from jeepney import DBusAddress
from jeepney.bus_messages import MatchRule


class PropertiesChanged(MatchRule):
    interface = "org.freedesktop.DBus.Properties"
    member = "PropertiesChanged"

    def __init__(
        self,
        sender=None,
        object_path="/org/mpris/MediaPlayer2",
    ):
        super().__init__(
            type="signal",
            sender=sender,
            interface=self.interface,
            path=object_path,
            member=self.member,
        )


class TrackListReplaced(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"
    member = "TrackListReplaced"

    def __init__(
        self,
        sender=None,
        object_path="/org/mpris/MediaPlayer2",
    ):
        super().__init__(
            type="signal",
            sender=sender,
            interface=self.interface,
            path=object_path,
            member=self.member,
        )


class TrackAdded(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"
    member = "TrackAdded"

    def __init__(
        self,
        sender=None,
        object_path='/org/mpris/MediaPlayer2',
    ):
        super().__init__(
            type="signal",
            sender=sender,
            interface=PropertiesChanged.interface,
            path=object_path,
            member=self.member,
        )


class TrackRemoved(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"
    member = "TrackRemoved"

    def __init__(
        self,
        sender=None,
        object_path="/org/mpris/MediaPlayer2",
    ):
        super().__init__(
            type="signal",
            sender=sender,
            interface=PropertiesChanged.interface,
            path=object_path,
            member=self.member,
        )


class TrackMetadataChanged(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"
    member = "TrackMetadataChanged"

    def __init__(
        self,
        sender=None,
        object_path="/org/mpris/MediaPlayer2",
    ):
        super().__init__(
            type="signal",
            sender=sender,
            interface=PropertiesChanged.interface,
            path=object_path,
            member=self.member,
        )


class Seeked(MatchRule):
    interface = "org.mpris.MediaPlayer2.TrackList"
    member = "Seeked"

    def __init__(
        self,
        sender=None,
        object_path="/org/mpris/MediaPlayer2",
    ):
        super().__init__(
            type="signal",
            sender=sender,
            interface=Seeked.interface,
            path=object_path,
            member=self.member,
        )
