import subprocess

from django.core.files import File
from django_rq import job

from .converters import convert_to_hls, generate_thumbnail
from .functions import ALLOWED_RESOLUTIONS


@job
def process_video_task(video_id):
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
    source_path = video.source_file.path
    convert_all_resolutions(source_path, video.id)
    save_generated_thumbnail(video, source_path)


def convert_all_resolutions(source_path, video_id):
    for resolution in ALLOWED_RESOLUTIONS:
        convert_to_hls(source_path, video_id, resolution)


def save_generated_thumbnail(video, source_path):
    if video.thumbnail:
        return
    thumbnail_path = generate_thumbnail(source_path, video.id)
    with open(thumbnail_path, "rb") as thumbnail_file:
        video.thumbnail.save(thumbnail_path.name, File(thumbnail_file), save=True)


def mark_as_ready(video):
    video.status = video.STATUS_READY
    video.processing_error = ""
    video.save(update_fields=["status", "processing_error"])


def mark_as_failed(video, error):
    video.status = video.STATUS_FAILED
    video.processing_error = str(error)[:2000]
    video.save(update_fields=["status", "processing_error"])
