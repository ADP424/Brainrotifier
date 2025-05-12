import os
import numpy as np
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.audio.fx.all import audio_normalize

from CONSTANTS import INPUT_DIR, OUTPUT_DIR

def detect_pause(audio_clip, start_time=60, frame_duration=0.1, silence_thresh_db=-35, max_search=30):
    """Find a natural pause in audio after a given time using volume thresholds."""
    sample_rate = 44100
    samples_per_frame = int(sample_rate * frame_duration)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        audio_clip.write_audiofile(tmp_audio.name, fps=sample_rate, verbose=False, logger=None)
        audio_data = AudioFileClip(tmp_audio.name).to_soundarray(fps=sample_rate)

    # Convert stereo to mono if needed
    if audio_data.ndim == 2:
        audio_data = audio_data.mean(axis=1)

    total_frames = int(len(audio_data) / samples_per_frame)
    times = np.arange(total_frames) * frame_duration
    start_frame = int(start_time / frame_duration)
    max_frame = int((start_time + max_search) / frame_duration)

    for i in range(start_frame, min(max_frame, total_frames)):
        chunk = audio_data[i * samples_per_frame: (i + 1) * samples_per_frame]
        volume = 20 * np.log10(np.sqrt(np.mean(chunk ** 2)) + 1e-5)
        if volume < silence_thresh_db:
            return i * frame_duration  # Time of first detected pause

    return start_time + 10  # fallback

def split_video_naturally(video_path: str, output_dir: str):
    clip = VideoFileClip(video_path)
    total_duration = clip.duration
    t = 0
    part = 1

    while t < total_duration:
        end_guess = min(t + 90, total_duration)
        subclip = clip.subclip(t, end_guess)
        audio = subclip.audio.fx(audio_normalize)

        pause_time = detect_pause(audio, start_time=60)
        actual_end = min(t + pause_time, total_duration)

        print(f"Writing part {part}: {t:.2f} to {actual_end:.2f}")
        output_path = os.path.join(output_dir, f"clip_part_{part}.mp4")
        clip.subclip(t, actual_end).write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False)

        t = actual_end
        part += 1

if __name__ == "__main__":
    split_video_naturally(f"{INPUT_DIR}/input_video.mp4", f"{OUTPUT_DIR}/")
