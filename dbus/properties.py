from jeepney import Properties
from org_mpris_MediaPlayer2 import MediaPlayer2, Player, TrackList


class MediaPlayer2Properties(Properties):
    def __init__(self):
        super().__init__(MediaPlayer2())

    def Identity(self):
        return self.get("Identity")

    def DesktopEntry(self):
        return self.get("DesktopEntry")

    def SupportedMimeTypes(self):
        return self.get("SupportedMimeTypes")

    def SupportedUriSchemes(self):
        return self.get("SupportedUriSchemes")

    def HasTrackList(self):
        return self.get("HasTrackList")

    def CanQuit(self):
        return self.get("CanQuit")

    def CanSetFullscreen(self):
        return self.get("CanSetFullscreen")

    def Fullscreen(self):
        return self.get("Fullscreen")

    def CanRaise(self):
        return self.get("CanRaise")


class PlayerProperties(Properties):
    def __init__(self):
        super().__init__(Player())

    def Metadata(self):
        return self.get("Metadata")

    def PlaybackStatus(self):
        return self.get("PlaybackStatus")

    def LoopStatus(self):
        return self.get("LoopStatus")

    def Volume(self):
        return self.get("Volume")

    def Shuffle(self):
        return self.get("Shuffle")

    def Position(self):
        return self.get("Position")

    def Rate(self):
        return self.get("Rate")

    def MinimumRate(self):
        return self.get("MinimumRate")

    def MaximumRate(self):
        return self.get("MaximumRate")

    def CanControl(self):
        return self.get("CanControl")

    def CanPlay(self):
        return self.get("CanPlay")

    def CanPause(self):
        return self.get("CanPause")

    def CanSeek(self):
        return self.get("CanSeek")


class TrackListProperties(Properties):
    def __init__(self):
        super().__init__(TrackList())

    def Tracks(self):
        return self.get("Tracks")

    def CanEditTracks(self):
        return self.get("CanEditTracks")

