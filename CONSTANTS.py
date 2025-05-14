from moviepy import VideoFileClip


FONTS_DIR = "assets/fonts"
INPUT_DIR = "input"
OUTPUT_DIR = "output"
VIDEOS_DIR = "assets/videos"

MIN_LENGTH = 30
MAX_LENGTH = 60
BUFFER = 0.25
SILENCE_THRESHOLD = -30

SAMPLE_RATE = 44100

SHORT_WIDTH = 1080
SHORT_HEIGHT = 1920

BOTTOM_CLIPS = {
    "sand_asmr": VideoFileClip(f"{VIDEOS_DIR}/sand_asmr.mp4"),
    "subway_surfers": VideoFileClip(f"{VIDEOS_DIR}/subway_surfers.mp4"),
    "minecraft_parkour": VideoFileClip(f"{VIDEOS_DIR}/minecraft_parkour.mp4"),
    "baking_soda_asmr": VideoFileClip(f"{VIDEOS_DIR}/subway_surfers.mp4"),
    "power_washing": VideoFileClip(f"{VIDEOS_DIR}/subway_surfers.mp4"),
}
