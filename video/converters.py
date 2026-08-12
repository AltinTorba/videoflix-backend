import subprocess

from .functions import (
    RESOLUTION_SETTINGS,
    get_hls_directory,
    get_manifest_path,
    get_thumbnail_output_path,
)

# "nice -n 15": lowers FFMPEG's CPU priority so that the Gunicorn process
# (running in the same container) can keep responding to requests while a
# conversion is in progress (prevents WORKER TIMEOUT).
NICE_PREFIX = ["nice", "-n", "15"]


def convert_to_hls(source_path, movie_id, resolution):
    """Convert a source file into HLS segments and a manifest via FFMPEG.

    Args:
        source_path: Path to the original video file.
        movie_id: The video id (determines the output directory).
        resolution: Target resolution, e.g. "720p".

    Returns:
        Path: Path to the generated index.m3u8 file.
    """
    settings_for_res = RESOLUTION_SETTINGS[resolution]
    output_dir = get_hls_directory(movie_id, resolution)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_hls_command(source_path, settings_for_res, output_dir)
    subprocess.run(command, check=True, capture_output=True)
    return get_manifest_path(movie_id, resolution)


def build_ffmpeg_hls_command(source_path, settings_for_res, output_dir):
    """Build the FFMPEG command line for the HLS conversion.

    Args:
        source_path: Path to the original video file.
        settings_for_res: Dict with "scale" and "bitrate" for the resolution.
        output_dir: Target directory for manifest and segments.

    Returns:
        list[str]: Full FFMPEG command as an argument list.
    """
    return NICE_PREFIX + [
        "ffmpeg", "-y", "-i", str(source_path),
        "-threads", "2",
        "-vf", f"scale={settings_for_res['scale']}",
        "-c:a", "aac", "-ar", "48000", "-c:v", "h264",
        "-b:v", settings_for_res["bitrate"], "-crf", "20",
        "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(output_dir / "%03d.ts"),
        str(output_dir / "index.m3u8"),
    ]


def generate_thumbnail(source_path, movie_id):
    """Extract a still frame as a thumbnail via FFMPEG.

    Args:
        source_path: Path to the original video file.
        movie_id: The video id (determines the output filename).

    Returns:
        Path: Path to the generated JPEG thumbnail file.
    """
    output_path = get_thumbnail_output_path(movie_id)
    command = NICE_PREFIX + [
        "ffmpeg", "-y", "-i", str(source_path),
        "-ss", "00:00:02", "-vframes", "1", str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True)
    return output_path
