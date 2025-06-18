import argparse
import random
from moviepy import VideoFileClip, clips_array

from CONSTANTS import BOTTOM_CLIPS, INPUT_DIR, MAX_LENGTH, MIN_LENGTH, OUTPUT_DIR, SHORT_HEIGHT, SHORT_WIDTH
from model.Short import Short
from model.VideoShorts import VideoShorts


def add_bottom_clip(short: Short, bottom_clip: VideoFileClip = None):
    """
    Merge the short with another clip so that the bottom clip takes up 1/3 of the screen.

    Parameters
    ----------
    short: Short
        The short to add the bottom clip to.

    bottom_clip: VideoFileClip, optional
        The clip to add to the bottom of the short. If not given, choose a random one.
    """

    if bottom_clip is None:
        bottom_clip = BOTTOM_CLIPS[random.choice(list(BOTTOM_CLIPS.keys()))]

    target_short_height = 2 * SHORT_HEIGHT // 3
    target_bottom_clip_height = SHORT_HEIGHT // 3
    adjusted_clip = short.clip.resized(height=target_short_height)
    bottom_clip = (
        bottom_clip.without_audio()
        .subclipped(0, short.clip.duration)
        .with_fps(short.clip.fps)
        .resized(height=target_bottom_clip_height)
    )
    short.clip = clips_array([[adjusted_clip], [bottom_clip]]).resized(width=SHORT_WIDTH, height=SHORT_HEIGHT)


def make_vertical(short: Short):
    width, height = short.clip.size
    new_width = int(height * 9 / 16)
    x_center = width // 2
    x1 = x_center - new_width // 2
    x2 = x_center + new_width // 2
    short.clip = short.clip.cropped(x1=x1, y1=0, x2=x2, y2=height)


def main(
    movie_name: str,
    movie_extension: str,
    min_length: int = MIN_LENGTH,
    max_length: int = MAX_LENGTH,
    do_bottom_clip: bool = True,
    do_subtitles: bool = True,
    stage: str = "prod",
):
    video_shorts = VideoShorts(f"{INPUT_DIR}/", f"{movie_name}.{movie_extension}", min_length, max_length, do_subtitles)

    for i, short in enumerate(video_shorts.shorts):
        if do_bottom_clip:
            add_bottom_clip(short)
        make_vertical(short)

        short.clip.write_videofile(
            f"{OUTPUT_DIR}/{movie_name}_{"test_" if stage == "dev" else ""}{i + 1}.mp4",
            codec="libx264",
            audio_codec="aac",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert text into Minecraft books.")

    parser.add_argument(
        "-i",
        "--input",
        default=None,
        required=True,
        help="The name of the input file to convert, including the file extension.",
        dest="input",
    )
    parser.add_argument(
        "-min",
        "--min-length",
        type=int,
        default=MIN_LENGTH,
        help="The minimum length of each short in seconds. Default is 45.",
        dest="min_length",
    )
    parser.add_argument(
        "-max",
        "--max-length",
        type=int,
        default=MAX_LENGTH,
        help="The maximum length of each short in seconds. Default is 60.",
        dest="max_length",
    )
    parser.add_argument(
        "-nbc",
        "--no-bottom-clip",
        action="store_false",
        help="Disable adding a random extra clip (e.g. subway surfers) on the bottom of each short.",
        dest="bottom_clip",
    )
    parser.add_argument(
        "-ns",
        "--no-subtitles",
        action="store_false",
        help="Disable adding subtitles to each short.",
        dest="subtitles",
    )
    args = parser.parse_args()

    movie_name, movie_extension = args.input.split(".")

    main(
        movie_name,
        movie_extension,
        min_length=args.min_length,
        max_length=args.max_length,
        do_bottom_clip=args.bottom_clip,
        do_subtitles=args.subtitles,
        stage="dev",
    )
