from django.http import FileResponse, Http404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .functions import get_manifest_path, get_segment_path, is_valid_resolution
from .models import Video
from .serializers import VideoListSerializer


class VideoListView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoListSerializer
    permission_classes = [IsAuthenticated]


class HLSManifestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        if not is_valid_resolution(resolution):
            raise Http404
        path = get_manifest_path(movie_id, resolution)
        if not path.exists():
            raise Http404
        return FileResponse(open(path, "rb"), content_type="application/vnd.apple.mpegurl")


class HLSSegmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        if not is_valid_resolution(resolution):
            raise Http404
        path = get_segment_path(movie_id, resolution, segment)
        if not path.exists():
            raise Http404
        return FileResponse(open(path, "rb"), content_type="video/MP2T")
