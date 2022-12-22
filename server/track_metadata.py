class TrackMetadata:
    "VLC track metadata"

    def __init__(self, trackId, uri, length):
        self.trackId = (trackId,)
        self.uri = uri
        self.length = length

    @staticmethod
    def fromMPRISMetadata(reply):
        # Track metadata is an array of string-variant pairs, where a variant is a
        # tuple with string-encoded type and the value
        result = {}
        for key, variant in reply.items():
            _, value = variant  # we don't really need the type
            result[key] = value
        return TrackMetadata(
            result.get("mpris:trackid", None),
            result.get("xesam:url", None),
            result.get("mpris:length", None),
        )
