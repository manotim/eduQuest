from django.urls import path
from . import views

app_name = "quizzes"

urlpatterns = [
    path("", views.QuizListView.as_view(), name="quiz_list"),
    path("<int:pk>/", views.QuizDetailView.as_view(), name="quiz_detail"),
    path("<int:pk>/start/", views.TakeQuizView.as_view(), name="take_quiz"),
    path("<int:pk>/leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:pk>/api/", views.QuizAPI.as_view(), name="quiz_api"),  # <-- new
]
