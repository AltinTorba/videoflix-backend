from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin view for video objects, including conversion status."""

    list_display = ["id", "title", "category", "status", "created_at"]
    list_filter = ["status", "category"]
    readonly_fields = ["thumbnail", "status", "processing_error"]
