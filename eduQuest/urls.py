from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include  

urlpatterns = [
    path("admin/", admin.site.urls),
    path("quizzes/", include("quizzes.urls")),   # ✅ mount under /quizzes/
    path("accounts/", include("django.contrib.auth.urls")),
]
