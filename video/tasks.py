from django.core.files import File
from django_rq import job

from .converters import convert_to_hls, generate_thumbnail
from .functions import ALLOWED_RESOLUTIONS


@job
def process_video_task(video_id):
    from .models import Video

    video = Video.objects.get(pk=video_id)
    source_path = video.source_file.path
    convert_all_resolutions(source_path, video_id)
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
