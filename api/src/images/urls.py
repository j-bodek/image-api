from django.urls import path
from images import views as img_views

app_name = "images"
urlpatterns = [
    path("image/upload/", img_views.ImageUploadView.as_view(), name="image_upload"),
]
