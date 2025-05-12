import os
from pydub import AudioSegment
from pydub.silence import detect_silence
import tempfile
from moviepy import VideoFileClip, AudioFileClip
from moviepy.audio.fx import AudioNormalize

from CONSTANTS import INPUT_DIR, BUFFER, MAX_LENGTH, MIN_LENGTH, OUTPUT_DIR, SILENCE_THRESHOLD


def detect_pause(
    video_clip: VideoFileClip,
    start_time: int | float = MIN_LENGTH,
    end_time: int | float = MAX_LENGTH,
    silence_thresh_db: int | float = SILENCE_THRESHOLD,
):
    """
    Find a natural pause in audio after a given time using volume thresholds.
    """

    sample_rate = 44100

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        video_clip.subclipped(start_time, end_time).audio.write_audiofile(tmp_audio.name, fps=sample_rate)
        audio_seg = AudioSegment.from_wav(tmp_audio.name)

    silence_segments = detect_silence(audio_seg, min_silence_len=1000, silence_thresh=silence_thresh_db)
    if len(silence_segments) > 0:
        start_silence: float = silence_segments[0][0] / 1000
        return start_time + start_silence + BUFFER
    return end_time


def split_video_naturally(video_path: str, output_dir: str):
    clip = VideoFileClip(video_path)
    total_duration: float = clip.duration
    curr_time = 0
    part = 1

    while curr_time < total_duration:
        end_guess = min(curr_time + MAX_LENGTH, total_duration)
        subclip: VideoFileClip = clip.subclipped(curr_time, end_guess)
        audio: AudioFileClip = subclip.with_effects([AudioNormalize()])

        pause_time = detect_pause(audio)
        actual_end = min(curr_time + pause_time, total_duration)

        print(f"Writing part {part}: {curr_time:.2f} to {actual_end:.2f}")
        output_path = os.path.join(output_dir, f"clip_part_{part}.mp4")
        clip.subclipped(curr_time, actual_end).write_videofile(output_path, codec="libx264", audio_codec="aac")

        curr_time = actual_end
        part += 1


if __name__ == "__main__":
    split_video_naturally(f"{INPUT_DIR}/aardman_classics.mp4", f"{OUTPUT_DIR}/")
