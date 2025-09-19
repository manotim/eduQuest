from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = settings.AUTH_USER_MODEL


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)


    def __str__(self):
        return self.name
    
class Quiz(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, related_name='quizzes', on_delete=models.SET_NULL, null=True, blank=True)
    time_per_question = models.PositiveIntegerField(help_text='Seconds per question', default=30)
    randomize_questions = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=True)


    def __str__(self):
        return self.title
    
class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    # optional per-question override of time (seconds)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Override quiz time per question')


    def __str__(self):
        return f"{self.quiz.title} - Q{self.pk}"
    


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)


    def __str__(self):
        return self.text[:60]
    
class QuizAttempt(models.Model):
    user = models.ForeignKey(User, related_name='quiz_attempts', on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name='attempts', on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # store randomized question order and any per-question metadata
    question_order = models.JSONField(default=list) # [question_id, ...]
    answers = models.JSONField(default=dict) # {question_id: {choice_id, correct: bool, time_taken:sec}}
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)


    class Meta:
        ordering = ['-score', 'finished_at']


    def __str__(self):
        return f"Attempt {self.pk} - {self.user} - {self.quiz}"
    


class QuestionAttempt(models.Model):
    attempt = models.ForeignKey(QuizAttempt, related_name='question_attempts', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL)
    correct = models.BooleanField(default=False)
    time_taken = models.PositiveIntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"QA {self.attempt.pk} - Q{self.question.pk}"