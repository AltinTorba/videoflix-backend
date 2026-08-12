from django.core.cache import cache
from django.http import FileResponse, Http404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .functions import get_manifest_path, get_segment_path, is_valid_resolution
from .models import Video
from .serializers import VideoListSerializer

VIDEO_LIST_CACHE_KEY = "video_list"
VIDEO_LIST_CACHE_TTL = 300


class VideoListView(ListAPIView):
    """Returns the list of all videos, cached in Redis."""

    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """Return the video list from cache, or build and cache it.

        Args:
            request: The incoming HTTP request.
            *args: Additional positional arguments (unused).
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Response: 200 with the list of all videos.
        """
        cached_data = cache.get(VIDEO_LIST_CACHE_KEY)
        if cached_data is not None:
            return Response(cached_data)
        return self._build_and_cache_response()

    def _build_and_cache_response(self):
        """Serialize the video list and store it in the cache.

        Returns:
            Response: 200 with the freshly built video list.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        cache.set(VIDEO_LIST_CACHE_KEY, serializer.data, VIDEO_LIST_CACHE_TTL)
        return Response(serializer.data)


class HLSManifestView(APIView):
    """Returns the index.m3u8 manifest file for a video and resolution."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """Return the HLS manifest as a file response.

        Args:
            request: The incoming HTTP request.
            movie_id: The video id.
            resolution: Requested resolution, e.g. "720p".

        Returns:
            FileResponse: The m3u8 manifest.

        Raises:
            Http404: If the resolution is invalid or the file is missing.
        """
        if not is_valid_resolution(resolution):
            raise Http404
        path = get_manifest_path(movie_id, resolution)
        if not path.exists():
            raise Http404
        return FileResponse(open(path, "rb"), content_type="application/vnd.apple.mpegurl")


class HLSSegmentView(APIView):
    """Returns a single HLS video segment (.ts)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """Return a binary .ts segment.

        Args:
            request: The incoming HTTP request.
            movie_id: The video id.
            resolution: Requested resolution.
            segment: Filename of the requested segment.

        Returns:
            FileResponse: The binary video segment.

        Raises:
            Http404: If the resolution is invalid or the file is missing.
        """
        if not is_valid_resolution(resolution):
            raise Http404
        path = get_segment_path(movie_id, resolution, segment)
        if not path.exists():
            raise Http404
        return FileResponse(open(path, "rb"), content_type="video/MP2T")
