from rest_framework import serializers

from .models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """Serializes Video objects for the list view (/api/video/)."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ["id", "created_at", "title", "description", "thumbnail_url", "category"]

    def get_thumbnail_url(self, obj):
        """Build the absolute URL to the thumbnail image.

        Args:
            obj: The video object.

        Returns:
            str | None: Absolute thumbnail URL, or None if no thumbnail
            is set.
        """
        request = self.context.get("request")
        return request.build_absolute_uri(obj.thumbnail.url) if obj.thumbnail else None
