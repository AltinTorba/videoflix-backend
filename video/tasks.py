import subprocess

from django.core.files import File
from django_rq import job

from .converters import convert_to_hls, generate_thumbnail
from .functions import ALLOWED_RESOLUTIONS


@job
def process_video_task(video_id):
    """Django RQ job: converts a video into all target resolutions.

    Sets the status to "processing", runs the conversion, and sets it to
    "ready" or "failed" depending on the outcome.

    Args:
        video_id: The id of the video object to convert.
    """
    from .models import Video

    video = Video.objects.get(pk=video_id)
    video.status = Video.STATUS_PROCESSING
    video.save(update_fields=["status"])
    try:
        run_conversion(video)
    except subprocess.CalledProcessError as error:
        mark_as_failed(video, error)
    else:
        mark_as_ready(video)


def run_conversion(video):
    """Run the full conversion (all resolutions plus thumbnail).

    Args:
        video: The video object to convert.
    """
    source_path = video.source_file.path
    convert_all_resolutions(source_path, video.id)
    save_generated_thumbnail(video, source_path)


def convert_all_resolutions(source_path, video_id):
    """Convert the source file into every allowed resolution.

    Args:
        source_path: Path to the original video file.
        video_id: The video id.
    """
    for resolution in ALLOWED_RESOLUTIONS:
        convert_to_hls(source_path, video_id, resolution)


def save_generated_thumbnail(video, source_path):
    """Generate a thumbnail if needed and attach it to the video object.

    Args:
        video: The video object (thumbnail is only set if currently empty).
        source_path: Path to the original video file.
    """
    if video.thumbnail:
        return
    thumbnail_path = generate_thumbnail(source_path, video.id)
    with open(thumbnail_path, "rb") as thumbnail_file:
        video.thumbnail.save(thumbnail_path.name, File(thumbnail_file), save=True)


def mark_as_ready(video):
    """Set the conversion status to "ready" and clear any error message.

    Args:
        video: The successfully converted video object.
    """
    video.status = video.STATUS_READY
    video.processing_error = ""
    video.save(update_fields=["status", "processing_error"])


def mark_as_failed(video, error):
    """Set the conversion status to "failed" and store the error message.

    Args:
        video: The video object whose conversion failed.
        error: The exception that occurred (stored as text).
    """
    video.status = video.STATUS_FAILED
    video.processing_error = str(error)[:2000]
    video.save(update_fields=["status", "processing_error"])
