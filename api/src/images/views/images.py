from rest_framework import generics, permissions
from images.serializers import ImageSerializer
from core.models import Image
from django.db.models.query import QuerySet


class ImageListView(generics.ListAPIView):
    """View used to get list of images created by authenticated user"""

    serializer_class = ImageSerializer
    queryset = Image.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        """Return a queryset of Images created by authenticated user"""

        return self.queryset.filter(
            uploaded_by=self.request.user,
        ).order_by("-uploaded_at")
