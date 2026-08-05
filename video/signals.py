from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Video
from .tasks import process_video_task
from .views import VIDEO_LIST_CACHE_KEY


@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    cache.delete(VIDEO_LIST_CACHE_KEY)
    if created and instance.source_file:
        process_video_task.delay(instance.id)


@receiver(post_delete, sender=Video)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    cache.delete(VIDEO_LIST_CACHE_KEY)
