from django.urls import path, re_path
from images import views as img_views

app_name = "images"
urlpatterns = [
    # image listing endpoint
    path("images/", img_views.ImageListView.as_view(), name="image_list"),
    # image upload endpoint
    path("image/upload/", img_views.ImageUploadView.as_view(), name="image_upload"),
    # expiring image endpoints
    path(
        "image/expiring/",
        img_views.GenerateExpiringImageView.as_view(),
        name="image_expiring_create",
    ),
    re_path(
        r"^image/expiring/(?P<token>(?:[a-zA-Z0-9_-]{4})*(?:[a-zA-Z0-9_-]{2}==|[a-zA-Z0-9_-]{3}=|[a-zA-Z0-9_-]{4}))/(?P<path>.*)$",
        img_views.ExpiringImageView.as_view(),
        name="image_expiring",
    ),
]
