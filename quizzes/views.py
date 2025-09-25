from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from .models import Quiz, Question, Choice, QuizAttempt, QuestionAttempt
from django.contrib.auth.forms import UserCreationForm



def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # ✅ creates the user
            return redirect("login")  # go to login after register
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

class QuizListView(ListView):
    model = Quiz
    template_name = 'quizzes/quiz_list.html'
    queryset = Quiz.objects.filter(published=True)

class QuizDetailView(DetailView):
    model = Quiz
    template_name = 'quizzes/quiz_detail.html'

class TakeQuizView(LoginRequiredMixin, TemplateView):
    template_name = 'quizzes/take_quiz.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz_id = kwargs.get("pk")
        quiz = get_object_or_404(Quiz, id=quiz_id)

        question_ids = list(quiz.questions.values_list("id", flat=True))
        if quiz.randomize_questions:
            from random import sample
            question_ids = sample(question_ids, len(question_ids))

        attempt, created = QuizAttempt.objects.get_or_create(
            quiz=quiz,
            user=self.request.user,
            defaults={"question_order": question_ids}
        )
        if not attempt.question_order:
            attempt.question_order = question_ids
            attempt.save()

        context["attempt"] = attempt
        return context

class QuizAPI(LoginRequiredMixin, View):
    def get(self, request, pk):
        attempt = get_object_or_404(QuizAttempt, quiz_id=pk, user=request.user)
        q_index = int(request.GET.get("q", 0))

        # If user finished all questions
        if q_index >= len(attempt.question_order):
            return JsonResponse({"finished": True})

        question_id = attempt.question_order[q_index]
        question = get_object_or_404(Question, id=question_id)

        return JsonResponse({
            "finished": False,
            "total": len(attempt.question_order),
            "question": question.text,
            "choices": list(question.choices.values("id", "text")),
            "time_limit": question.time_limit or attempt.quiz.time_per_question,
        })

    def post(self, request, pk):
        attempt = get_object_or_404(QuizAttempt, quiz_id=pk, user=request.user)
        q_index = int(request.GET.get("q", 0))
        body = json.loads(request.body)

        question_id = attempt.question_order[q_index]
        question = get_object_or_404(Question, id=question_id)
        choice = get_object_or_404(Choice, id=body["choice_id"], question=question)

        # Save answer
        attempt.answers[str(question.id)] = {
            "choice_id": choice.id,
            "correct": choice.is_correct,
            "time_taken": body.get("time_taken", 0),
        }
        attempt.save()

        return JsonResponse({"ok": True, "correct": choice.is_correct})

class QuestionDataView(LoginRequiredMixin, View):
    def get(self, request, attempt_id, q_index):
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        try:
            q_index = int(q_index)
            qid = attempt.question_order[q_index]
        except Exception:
            return HttpResponseBadRequest('Invalid question index')
        q = get_object_or_404(Question, id=qid)
        choices = list(q.choices.values('id', 'text'))
        data = {
        'question_id': q.id,
        'text': q.text,
        'choices': choices,
        'index': q_index,
        'total': len(attempt.question_order),
        'time_limit': q.time_limit or attempt.quiz.time_per_question,
        }
        return JsonResponse(data)
    
# AJAX endpoint: submit answer for one question
class SubmitAnswerView(LoginRequiredMixin, View):
    def post(self, request, attempt_id):
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        body = json.loads(request.body)
        question_id = body.get('question_id')
        choice_id = body.get('choice_id')
        time_taken = body.get('time_taken')
        q = get_object_or_404(Question, id=question_id)
        choice = None
        if choice_id:
            choice = get_object_or_404(Choice, id=choice_id, question=q)
        correct = choice.is_correct if choice else False
        # store into QuestionAttempt model
        qa = attempt.question_attempts.get(question_id=question_id)
        qa.choice = choice
        qa.correct = correct
        qa.time_taken = int(time_taken) if time_taken is not None else None
        qa.answered_at = timezone.now()
        qa.save()
        # update compact answers JSON
        answers = attempt.answers
        answers[str(question_id)] = {'choice_id': choice_id, 'correct': correct, 'time_taken': time_taken}
        attempt.answers = answers
        attempt.save()
        return JsonResponse({'ok': True, 'correct': correct})
    
# AJAX endpoint: finish quiz
class FinishQuizView(LoginRequiredMixin, View):
    def post(self, request, attempt_id):
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        if attempt.finished_at:
            return JsonResponse({'ok': True})
        # compute score
        total = attempt.question_attempts.count()
        correct_count = attempt.question_attempts.filter(correct=True).count()
        score = (correct_count / total) * 100 if total else 0
        attempt.score = round(score, 2)
        attempt.finished_at = timezone.now()
        # duration
        attempt.duration_seconds = int((attempt.finished_at - attempt.started_at).total_seconds())
        attempt.save()
        return JsonResponse({'ok': True, 'score': attempt.score})
    
# Leaderboard view
class LeaderboardView(ListView):
    template_name = 'quizzes/leaderboard.html'
    model = QuizAttempt
    paginate_by = 50


    def get_queryset(self):
        quiz_slug = self.kwargs.get('slug')
        quiz = g

class ResultsView(LoginRequiredMixin, TemplateView):
    template_name = "quizzes/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = get_object_or_404(Quiz, pk=self.kwargs["pk"])
        attempt = get_object_or_404(
            QuizAttempt,
            quiz=quiz,
            user=self.request.user
        )

        results = []
        correct_count = 0
        total_questions = quiz.questions.count()

        for question in quiz.questions.all():
            # Look up this question in the JSON answers
            answer_data = attempt.answers.get(str(question.id))
            selected_text = "No answer"
            is_correct = False

            if answer_data:
                try:
                    selected_choice = Choice.objects.get(id=answer_data["choice_id"])
                    selected_text = selected_choice.text
                    is_correct = answer_data.get("correct", False)
                except Choice.DoesNotExist:
                    selected_text = "Invalid choice"

            # The correct choice(s)
            correct_choice = question.choices.filter(is_correct=True).first()
            correct_text = correct_choice.text if correct_choice else "N/A"

            if is_correct:
                correct_count += 1

            results.append({
                "question": question.text,
                "selected": selected_text,
                "correct_answer": correct_text,
                "correct": is_correct,
            })

        context["quiz"] = quiz
        context["attempt"] = attempt
        context["results"] = results
        context["score"] = correct_count
        context["total"] = total_questions
        return context



class LeaderboardView(DetailView):
    model = Quiz
    template_name = "quizzes/leaderboard.html"
    context_object_name = "quiz"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        context["leaderboard"] = (
            QuizAttempt.objects.filter(quiz=quiz)
            .select_related("user")
            .order_by("-score", "created_at")[:10]
        )
        return context