import os
import sys
from pydub import AudioSegment
from pydub.silence import detect_silence
import tempfile
from moviepy import VideoFileClip, AudioFileClip
from moviepy.audio.fx import AudioNormalize

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from CONSTANTS import BUFFER, MAX_LENGTH, MIN_LENGTH, SAMPLE_RATE, SILENCE_THRESHOLD


class VideoShorts:

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.shorts: list[VideoFileClip] = []
        self._split_video()

    def _split_video(self):
        self.full_movie = VideoFileClip(self.video_path)
        total_duration: float = self.full_movie.duration
        curr_time = 0
        part = 1

        while curr_time < total_duration:
            end_guess = min(curr_time + MAX_LENGTH, total_duration)
            subclip: VideoFileClip = self.full_movie.subclipped(curr_time, end_guess)
            audio: AudioFileClip = subclip.with_effects([AudioNormalize()])

            pause_time, resume_time = self._detect_pause(audio)
            actual_end = min(curr_time + pause_time, total_duration)
            actual_resume = min(curr_time + resume_time, total_duration)

            print(f"Writing part {part}: {curr_time:.2f} to {actual_end:.2f}")
            self.shorts.append(self.full_movie.subclipped(curr_time, actual_end))

            curr_time = actual_resume
            part += 1

    def _detect_pause(
        self,
        video_clip: VideoFileClip,
        start_time: int | float = MIN_LENGTH,
        end_time: int | float = MAX_LENGTH,
        silence_thresh_db: int | float = SILENCE_THRESHOLD,
    ):
        """
        Find a natural pause in audio after a given time using volume thresholds.
        """

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            duration: float = video_clip.duration
            if duration <= start_time:
                return duration, duration
            video_clip.subclipped(start_time, end_time).audio.write_audiofile(tmp_audio.name, fps=SAMPLE_RATE)
            audio_seg = AudioSegment.from_wav(tmp_audio.name)

        silence_segments = detect_silence(audio_seg, min_silence_len=1000, silence_thresh=silence_thresh_db)
        if len(silence_segments) > 0:
            start_silence: float = silence_segments[0][0] / 1000
            end_silence: float = silence_segments[0][1] / 1000
            return start_time + start_silence + BUFFER, start_time + end_silence
        return end_time, end_time
