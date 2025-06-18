import os
import sys
from pydub import AudioSegment
from pydub.silence import detect_silence
import tempfile
from moviepy import CompositeVideoClip, TextClip, VideoFileClip, AudioFileClip
from moviepy.audio.fx import AudioNormalize
from faster_whisper import WhisperModel
from faster_whisper.transcribe import Word

from model.Short import Short

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from CONSTANTS import BUFFER, FONTS_DIR, MAX_LENGTH, MIN_LENGTH, SAMPLE_RATE, SILENCE_THRESHOLD


class VideoShorts:

    def __init__(
        self,
        video_folder_path: str,
        video_file_name: str,
        min_length: int = MIN_LENGTH,
        max_length: int = MAX_LENGTH,
        add_subtitles: bool = True,
    ):
        self.video_folder_path = video_folder_path
        self.video_file_name = video_file_name
        self.video_path = f"{video_folder_path}/{video_file_name}"

        self.min_length = min_length
        self.max_length = max_length

        self.add_subtitles = add_subtitles

        self.full_subtitles: list[Word] = []
        if add_subtitles:
            self._get_subtitles()

        self.full_movie = None
        self.shorts: list[Short] = []
        self._split_video()

    def _split_video(self):
        self.full_movie = VideoFileClip(self.video_path)
        total_duration: float = self.full_movie.duration
        curr_time = 0
        part = 1

        subtitle_index = 0
        while curr_time < total_duration:
            end_guess = min(curr_time + MAX_LENGTH, total_duration)
            subclip: VideoFileClip = self.full_movie.subclipped(curr_time, end_guess)
            audio: AudioFileClip = subclip.with_effects([AudioNormalize()])

            pause_time, resume_time = self._detect_pause(audio, self.min_length, self.max_length)
            actual_end = min(curr_time + pause_time, total_duration)
            actual_resume = min(curr_time + resume_time, total_duration)

            print(f"Writing part {part}: {curr_time:.2f} to {actual_end:.2f}")
            short = Short(self.full_movie.subclipped(curr_time, actual_end), curr_time, actual_end)

            short_transcript: list[Word] = []
            subtitle_clips: list[VideoFileClip] = []
            while (
                0 <= subtitle_index < len(self.full_subtitles) and self.full_subtitles[subtitle_index].start < short.end_time
            ):
                word = self.full_subtitles[subtitle_index]
                short_transcript.append(word)
                text = word.word.strip()

                sub_start = max(word.start - short.start_time, 0)
                sub_duration = min(word.end - sub_start - short.start_time, short.clip.duration - sub_start)
                text_clip = (
                    TextClip(
                        font=f"{FONTS_DIR}/lato_bold.otf",
                        text=text,
                        font_size=72,
                        size=(1080, 200),
                        color="white",
                        stroke_color="black",
                        stroke_width=8,
                        method="caption",
                        text_align="center",
                    )
                    .with_position(("center", "center"))
                    .with_duration(sub_duration)
                    .with_start(sub_start)
                )
                subtitle_clips.append(text_clip)

                subtitle_index += 1

            # words can run over between shorts
            subtitle_index -= 1

            short.clip = CompositeVideoClip([short.clip] + subtitle_clips)
            short.transcript = short_transcript
            self.shorts.append(short)

            curr_time = actual_resume
            part += 1

    def _detect_pause(
        self,
        video_clip: VideoFileClip,
        start_time: int | float,
        end_time: int | float,
        silence_thresh_db: int | float = SILENCE_THRESHOLD,
    ):
        """
        Find a natural pause in audio after a given time using volume thresholds.
        """

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            duration: float = video_clip.duration
            if duration <= start_time:
                return duration, duration
            video_clip.subclipped(start_time, min(end_time, duration)).audio.write_audiofile(
                tmp_audio.name, fps=SAMPLE_RATE
            )
            audio_seg = AudioSegment.from_wav(tmp_audio.name)

        silence_segments = detect_silence(audio_seg, min_silence_len=1000, silence_thresh=silence_thresh_db)
        if len(silence_segments) > 0:
            start_silence: float = silence_segments[0][0] / 1000
            end_silence: float = silence_segments[0][1] / 1000
            return start_time + start_silence + BUFFER, start_time + end_silence
        return end_time, end_time

    def _get_subtitles(self) -> list[Word]:
        model = WhisperModel("small", compute_type="int8", device="cpu")
        movie = VideoFileClip(self.video_path)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
            movie.audio.write_audiofile(tmp_audio.name, fps=SAMPLE_RATE)
            segments, _ = model.transcribe(
                self.video_path, beam_size=5, vad_filter=True, word_timestamps=True, no_speech_threshold=0.5
            )

        for segment in segments:
            print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
            for word in segment.words:
                print(f"\t[{word.start:.2f}s - {word.end:.2f}s] {word.word}")
                self.full_subtitles.append(word)
