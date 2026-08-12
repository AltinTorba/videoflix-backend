from pathlib import Path

from django.conf import settings

ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}

RESOLUTION_SETTINGS = {
    "480p": {"scale": "854:480", "bitrate": "1400k"},
    "720p": {"scale": "1280:720", "bitrate": "2800k"},
    "1080p": {"scale": "1920:1080", "bitrate": "5000k"},
}


def get_hls_directory(movie_id, resolution):
    """Return the target directory for a video's HLS files at a resolution.

    Args:
        movie_id: The video id.
        resolution: Target resolution, e.g. "720p".

    Returns:
        Path: Path to the HLS folder (media/videos/hls/<id>/<resolution>/).
    """
    return Path(settings.MEDIA_ROOT) / "videos" / "hls" / str(movie_id) / resolution


def get_manifest_path(movie_id, resolution):
    """Return the path to the index.m3u8 manifest file.

    Args:
        movie_id: The video id.
        resolution: Target resolution.

    Returns:
        Path: Path to the manifest file.
    """
    return get_hls_directory(movie_id, resolution) / "index.m3u8"


def get_segment_path(movie_id, resolution, segment):
    """Return the path to a single HLS segment (.ts) file.

    Args:
        movie_id: The video id.
        resolution: Target resolution.
        segment: Segment filename (sanitized to prevent path traversal).

    Returns:
        Path: Path to the segment file.
    """
    safe_segment = Path(segment).name
    return get_hls_directory(movie_id, resolution) / safe_segment


def is_valid_resolution(resolution):
    """Check whether the requested resolution is supported.

    Args:
        resolution: The resolution to validate.

    Returns:
        bool: True if the resolution is in ALLOWED_RESOLUTIONS.
    """
    return resolution in ALLOWED_RESOLUTIONS


def get_thumbnail_output_path(movie_id):
    """Return the target path for the auto-generated thumbnail.

    Args:
        movie_id: The video id.

    Returns:
        Path: Path to the thumbnail file (directory created if needed).
    """
    directory = Path(settings.MEDIA_ROOT) / "thumbnails" / "generated"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{movie_id}.jpg"
