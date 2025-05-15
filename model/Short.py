from moviepy import CompositeVideoClip, VideoFileClip
from faster_whisper.transcribe import Word


class Short:
    """
    Represents a single short stemming from a movie.
    """

    def __init__(
        self,
        clip: VideoFileClip | CompositeVideoClip,
        start_time: float,
        end_time: float,
        transcript: list[Word] = None,
    ):
        self.clip = clip
        self.start_time = start_time
        self.end_time = end_time
        self.transcript = transcript if transcript is not None else []
