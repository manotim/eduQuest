let currentQuestionIndex = 0;
let quizId = null;
let totalQuestions = 0;

function startQuiz(qid) {
  quizId = qid;
  currentQuestionIndex = 0;
  loadQuestion();
}

function loadQuestion() {
  fetch(`/quizzes/${quizId}/api/?q=${currentQuestionIndex}`)
    .then(res => res.json())
    .then(data => {
      if (data.finished) {
        // Redirect to results page when quiz is done
        window.location.href = `/quizzes/${quizId}/results/`;
        return;
      }

      totalQuestions = data.total;
      renderQuestion(data);
    })
    .catch(err => console.error("Load question error:", err));
}

function renderQuestion(data) {
  const container = document.getElementById("quiz-container");
  container.innerHTML = `
    <div class="mb-4">
      <h2 class="text-xl font-semibold">${data.question}</h2>
      <p class="text-sm text-gray-500">Question ${currentQuestionIndex + 1} of ${data.total}</p>
    </div>
    <ul class="space-y-2">
      ${data.choices.map(choice => `
        <li>
          <button onclick="submitAnswer(${choice.id})"
            class="w-full text-left px-4 py-2 border rounded hover:bg-gray-100">
            ${choice.text}
          </button>
        </li>
      `).join("")}
    </ul>
    <div id="timer" class="mt-4 text-red-600 font-bold"></div>
  `;

  startTimer(data.time_limit);
}

function submitAnswer(choiceId) {
  fetch(`/quizzes/${quizId}/api/?q=${currentQuestionIndex}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ choice_id: choiceId })
  })
    .then(res => res.json())
    .then(data => {
      currentQuestionIndex++;
      if (currentQuestionIndex >= totalQuestions) {
        // Quiz finished → redirect to results
        window.location.href = `/quizzes/${quizId}/results/`;
      } else {
        loadQuestion();
      }
    })
    .catch(err => console.error("Submit answer error:", err));
}

function startTimer(seconds) {
  let remaining = seconds;
  const timerEl = document.getElementById("timer");
  const interval = setInterval(() => {
    timerEl.textContent = `Time left: ${remaining}s`;
    if (remaining <= 0) {
      clearInterval(interval);
      // Auto-skip if time runs out
      currentQuestionIndex++;
      if (currentQuestionIndex >= totalQuestions) {
        window.location.href = `/quizzes/${quizId}/results/`;
      } else {
        loadQuestion();
      }
    }
    remaining--;
  }, 1000);
}

function getCSRFToken() {
  const cookieValue = document.cookie
    .split("; ")
    .find(row => row.startsWith("csrftoken="));
  return cookieValue ? cookieValue.split("=")[1] : "";
}
