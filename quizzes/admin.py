from django.contrib import admin
from .models import Category, Quiz, Question, Choice, QuizAttempt, QuestionAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('quiz', 'text', 'order')
    list_filter = ('quiz',)


class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published', 'created_at')
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Category)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizAttempt)
admin.site.register(QuestionAttempt)