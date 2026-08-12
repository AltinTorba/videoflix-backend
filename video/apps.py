from django.apps import AppConfig


class VideoConfig(AppConfig):
    """App configuration for the video app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "video"

    def ready(self):
        """Register the signal handlers when the app starts."""
        import video.signals  # noqa: F401
