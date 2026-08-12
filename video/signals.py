from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Video
from .tasks import process_video_task
from .views import VIDEO_LIST_CACHE_KEY


@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    """Invalidate the video list cache and start the conversion.

    Triggered whenever a Video object is saved. The HLS conversion is
    only started as a background task on creation, and only if a source
    file is present.

    Args:
        sender: The model class (Video).
        instance: The saved video object.
        created: True if the object was newly created.
        **kwargs: Additional signal arguments (unused).
    """
    cache.delete(VIDEO_LIST_CACHE_KEY)
    if created and instance.source_file:
        process_video_task.delay(instance.id)


@receiver(post_delete, sender=Video)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Invalidate the video list cache after a video is deleted.

    Args:
        sender: The model class (Video).
        instance: The deleted video object.
        **kwargs: Additional signal arguments (unused).
    """
    cache.delete(VIDEO_LIST_CACHE_KEY)
