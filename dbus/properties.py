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

    def HasTrackLis(self):
        return self.get("HasTrackList")

    def CanQui(self):
        return self.get("CanQuit")

    def CanSetFullscree(self):
        return self.get("CanSetFullscreen")

    def Fullscree(self):
        return self.get("Fullscreen")

    def CanRais(self):
        return self.get("CanRaise")


class PlayerProperties(Properties):
    def __init__(self):
        super().__init__(Player())

    def Metadat(self):
        return self.get("Metadata")

    def PlaybackStatu(self):
        return self.get("PlaybackStatus")

    def LoopStatu(self):
        return self.get("LoopStatus")

    def Volum(self):
        return self.get("Volume")

    def Shuffl(self):
        return self.get("Shuffle")

    def Positio(self):
        return self.get("Position")

    def Rat(self):
        return self.get("Rate")

    def MinimumRat(self):
        return self.get("MinimumRate")

    def MaximumRat(self):
        return self.get("MaximumRate")

    def CanContro(self):
        return self.get("CanControl")

    def CanPla(self):
        return self.get("CanPlay")

    def CanPaus(self):
        return self.get("CanPause")

    def CanSee(self):
        return self.get("CanSeek")


class TrackListProperties(Properties):
    def __init__(self):
        super().__init__(TrackList())

    def Tracks(self):
        return self.get("Tracks")

    def CanEditTrack(self):
        return self.get("CanEditTracks")

