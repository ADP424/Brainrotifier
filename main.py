import random
from moviepy import VideoFileClip, clips_array

from CONSTANTS import BOTTOM_CLIPS, INPUT_DIR, OUTPUT_DIR, SHORT_HEIGHT, SHORT_WIDTH
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


def main(movie_name: str, movie_extension: str, stage: str = "prod"):
    video_shorts = VideoShorts(f"{INPUT_DIR}/", f"{movie_name}.{movie_extension}")

    for i, short in enumerate(video_shorts.shorts):
        add_bottom_clip(short)
        make_vertical(short)

        short.clip.write_videofile(
            f"{OUTPUT_DIR}/{movie_name}_{"test_" if stage == "dev" else ""}{i + 1}.mp4",
            codec="libx264",
            audio_codec="aac",
        )


if __name__ == "__main__":
    main("the_one_set", "mp4", stage="dev")
