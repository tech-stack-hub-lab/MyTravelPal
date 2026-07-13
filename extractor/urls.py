from django.urls import path
# from django.contrib.auth.views import LogoutView
from . import views

app_name = 'extractor'

urlpatterns = [
    path("upload_file/", views.upload_file, name="upload_file"),
    path("delete-upload/<int:id>/", views.delete_upload, name="delete_upload")
]