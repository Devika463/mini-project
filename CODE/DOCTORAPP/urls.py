from django.contrib import admin
from django.urls import path, include
from booking import views

urlpatterns = [
    path("", views.welcome, name="welcome"),   # Default welcome page
    path("admin/", admin.site.urls),
    path("", include("booking.urls")),
]
