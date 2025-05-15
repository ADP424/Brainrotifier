import random
import tempfile
from moviepy import CompositeVideoClip, TextClip, VideoFileClip, clips_array
from faster_whisper import WhisperModel
from faster_whisper.transcribe import Word

from CONSTANTS import BOTTOM_CLIPS, FONTS_DIR, INPUT_DIR, OUTPUT_DIR, SAMPLE_RATE, SHORT_HEIGHT, SHORT_WIDTH
from model.VideoShorts import VideoShorts
from  model.Summarize import summarize
from gtts import gTTS

def add_bottom_clip(short: VideoFileClip, bottom_clip: VideoFileClip = None) -> CompositeVideoClip:
    """
    Merge the short with another clip so that the bottom clip takes up 1/3 of the screen.

    Parameters
    ----------
    short: VideoFileClip
        The short to add the bottom clip to.

    bottom_clip: VideoFileClip, optional
        The clip to add to the bottom of the short. If not given, choose a random one.

    Returns
    -------
    CompositeVideoClip
        The short with the bottom clip attached.
    """

    if bottom_clip is None:
        bottom_clip = BOTTOM_CLIPS[random.choice(list(BOTTOM_CLIPS.keys()))]

    target_short_height = 2 * SHORT_HEIGHT // 3
    target_bottom_clip_height = SHORT_HEIGHT // 3
    short = short.resized(height=target_short_height)
    bottom_clip = (
        bottom_clip.without_audio()
        .subclipped(0, short.duration)
        .with_fps(short.fps)
        .resized(height=target_bottom_clip_height)
    )
    return clips_array([[short], [bottom_clip]]).resized(width=SHORT_WIDTH, height=SHORT_HEIGHT)


def make_vertical(short: VideoFileClip) -> VideoFileClip:
    width, height = short.size
    new_width = int(height * 9 / 16)
    x_center = width // 2
    x1 = x_center - new_width // 2
    x2 = x_center + new_width // 2

    return short.cropped(x1=x1, y1=0, x2=x2, y2=height)


def add_subtitles(short: VideoFileClip, words: list[Word], start_time: float) -> CompositeVideoClip:

    # quick binary search
    low = 0
    high = len(words)
    start_index = 0

    while low <= high:
        mid = (low + high) // 2

        if start_time < words[mid].start:
            high = mid - 1
        elif start_time > words[mid].end:
            low = mid + 1
        else:
            start_index = mid
            break

    subtitle_clips = []
    index = start_index
    while words[index].start <= start_time + short.duration:
        word = words[index]
        text = word.word.strip()

        if len(text) == 0:
            index += 1
            continue

        sub_start = max(word.start - start_time, 0)
        sub_duration = min(word.end - sub_start - start_time, short.duration - sub_start)
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

        index += 1

    return CompositeVideoClip([short] + subtitle_clips)


def get_subtitles(file_name: str) -> list[Word]:
    model = WhisperModel("small", compute_type="int8", device="cpu")

    movie = VideoFileClip(f"{INPUT_DIR}/{file_name}")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_audio:
        movie.audio.write_audiofile(tmp_audio.name, fps=SAMPLE_RATE)
        segments, _ = model.transcribe(
            f"{INPUT_DIR}/{file_name}", beam_size=5, vad_filter=True, word_timestamps=True, no_speech_threshold=0.5
        )
    print("Finished creating the segments!")

    audio_segments = []
    for segment in segments:
        print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
        for word in segment.words:
            print(f"\t[{word.start:.2f}s - {word.end:.2f}s] {word.word}")
            audio_segments.append(word)

    return audio_segments


def main(movie_name: str, movie_extension: str, stage: str = "prod"):
    video_shorts = VideoShorts(f"{INPUT_DIR}/{movie_name}.{movie_extension}")
    subtitles = get_subtitles(f"{movie_name}.{movie_extension}")

    subtitle_document = ""
    for subtitle in subtitles:
        subtitle_document += f"{subtitle.word}"

    summary = summarize(subtitle_document)
    tts = gTTS(summary)
    tts.save(f'{OUTPUT_DIR}/summary.mp3')

    print(f"[{subtitle_document}")
    print(subtitles)

    total_duration: float = 0
    for i, short in enumerate(video_shorts.shorts):
        short = add_bottom_clip(short)
        short = make_vertical(short)
        short = add_subtitles(short, subtitles, total_duration)
        short.write_videofile(
            f"{OUTPUT_DIR}/{movie_name}_{"exp_" if stage == "dev" else ""}{i + 1}.mp4",
            codec="libx264",
            audio_codec="aac",
        )

        total_duration += short.duration


if __name__ == "__main__":
    main("FastFoodGordon", "mov", stage="dev")
