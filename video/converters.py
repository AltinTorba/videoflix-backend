import subprocess

from .functions import (
    RESOLUTION_SETTINGS,
    get_hls_directory,
    get_manifest_path,
    get_thumbnail_output_path,
)


def convert_to_hls(source_path, movie_id, resolution):
    settings_for_res = RESOLUTION_SETTINGS[resolution]
    output_dir = get_hls_directory(movie_id, resolution)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_hls_command(source_path, settings_for_res, output_dir)
    subprocess.run(command, check=True, capture_output=True)
    return get_manifest_path(movie_id, resolution)


def build_ffmpeg_hls_command(source_path, settings_for_res, output_dir):
    return [
        "ffmpeg", "-y", "-i", str(source_path),
        "-vf", f"scale={settings_for_res['scale']}",
        "-c:a", "aac", "-ar", "48000", "-c:v", "h264",
        "-b:v", settings_for_res["bitrate"], "-crf", "20",
        "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(output_dir / "%03d.ts"),
        str(output_dir / "index.m3u8"),
    ]


def generate_thumbnail(source_path, movie_id):
    output_path = get_thumbnail_output_path(movie_id)
    command = [
        "ffmpeg", "-y", "-i", str(source_path),
        "-ss", "00:00:02", "-vframes", "1", str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True)
    return output_path
