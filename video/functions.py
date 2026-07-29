from pathlib import Path

from django.conf import settings

ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}

RESOLUTION_SETTINGS = {
    "480p": {"scale": "854:480", "bitrate": "1400k"},
    "720p": {"scale": "1280:720", "bitrate": "2800k"},
    "1080p": {"scale": "1920:1080", "bitrate": "5000k"},
}


def get_hls_directory(movie_id, resolution):
    return Path(settings.MEDIA_ROOT) / "videos" / "hls" / str(movie_id) / resolution


def get_manifest_path(movie_id, resolution):
    return get_hls_directory(movie_id, resolution) / "index.m3u8"


def get_segment_path(movie_id, resolution, segment):
    safe_segment = Path(segment).name
    return get_hls_directory(movie_id, resolution) / safe_segment


def is_valid_resolution(resolution):
    return resolution in ALLOWED_RESOLUTIONS


def get_thumbnail_output_path(movie_id):
    directory = Path(settings.MEDIA_ROOT) / "thumbnails" / "generated"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{movie_id}.jpg"
