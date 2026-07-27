from pathlib import Path

from django.conf import settings

ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}


def get_hls_directory(movie_id, resolution):
    return Path(settings.MEDIA_ROOT) / "videos" / "hls" / str(movie_id) / resolution


def get_manifest_path(movie_id, resolution):
    return get_hls_directory(movie_id, resolution) / "index.m3u8"


def get_segment_path(movie_id, resolution, segment):
    safe_segment = Path(segment).name
    return get_hls_directory(movie_id, resolution) / safe_segment


def is_valid_resolution(resolution):
    return resolution in ALLOWED_RESOLUTIONS
