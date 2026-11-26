import { useState } from "react";
import { FiAward, FiCheckCircle, FiXCircle } from "react-icons/fi";
import { Alert, Badge, Button, EmptyState, Loadable, Table, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { formatDateTime, plural } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { Link } from "../lib/router.jsx";

export function ResultView({ result }) {
  return (
    <>
      <div className={`panel score ${result.passed ? "pass" : "fail"}`} role="status">
        {result.passed ? <FiCheckCircle aria-hidden="true" /> : <FiXCircle aria-hidden="true" />}
        <div>
          <h2>{result.passed ? "You passed!" : "Not passed yet"}</h2>
          <p><strong>{result.percentage}%</strong> ({result.score} of {result.total} correct). Pass mark: {result.pass_percentage}%.</p>
        </div>
      </div>
      {!result.answers_revealed && (
        <Alert>Correct answers are shown after you pass the quiz or use all attempts.</Alert>
      )}
      {result.review.map((item, number) => (
        <div key={number} className="panel question">
          <h3>{number + 1}. {item.prompt}</h3>
          <Badge tone={item.is_correct ? "success" : "danger"}>{item.is_correct ? "Correct" : "Incorrect"}</Badge>
          <ul className="review-options">
            {item.options.map((option, i) => {
              const chosen = i === item.chosen_index;
              const right = i === item.correct_index;
              return (
                <li key={i} className={`${chosen ? "chosen" : ""} ${right ? "right" : ""} ${chosen && !item.is_correct ? "wrong" : ""}`}>
                  <span>{option}</span>
                  <small>{[chosen && "Your answer", right && "Correct answer"].filter(Boolean).join(" · ")}</small>
                </li>
              );
            })}
          </ul>
          {item.explanation && <p className="meta">{item.explanation}</p>}
        </div>
      ))}
    </>
  );
}

export function Quiz({ params }) {
  const state = useApi(`/quizzes/${encodeURIComponent(params.id)}`);
  const toast = useToast();
  const [started, setStarted] = useState(false);
  const [answers, setAnswers] = useState({});
  const [outcome, setOutcome] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useTitle(state.data?.quiz.title || "Quiz");

  const begin = () => {
    setAnswers({});
    setOutcome(null);
    setError("");
    setStarted(true);
    window.scrollTo(0, 0);
  };

  return (
    <Loadable state={state}>
      {({ quiz, questions, attempts, can_attempt: canAttempt, preview, course_title: courseTitle }) => {
        const answered = Object.keys(answers).length;
        const submit = async (event) => {
          event.preventDefault();
          const missing = questions.find((q) => answers[q.id] === undefined);
          if (missing) {
            setError(`Please answer all questions. ${questions.length - answered} left.`);
            document.getElementById(`question-${missing.id}`)?.scrollIntoView({ block: "center" });
            return;
          }
          setBusy(true);
          setError("");
          try {
            const reply = await api.post(`/quizzes/${quiz.id}/submit`, { answers });
            setOutcome(reply);
            setStarted(false);
            window.scrollTo(0, 0);
            if (reply.progress?.is_completed) toast.success("Course completed! Your certificate is ready.");
            state.reload();
          } catch (problem) {
            setError(problem.message);
          } finally {
            setBusy(false);
          }
        };

        return (
          <div className="container section narrow">
            <p className="crumbs"><Link to={`/learn/${quiz.course_id}`}>{courseTitle}</Link> / {quiz.title}</p>
            <h1>{quiz.title}</h1>
            {quiz.description && <p>{quiz.description}</p>}
            <p className="meta">
              {plural(questions.length, "question")} · pass mark {quiz.pass_percentage}% ·{" "}
              {quiz.max_attempts ? `${attempts.length} of ${quiz.max_attempts} attempts used` : "unlimited attempts"}
            </p>

            {outcome && (
              <>
                <ResultView result={outcome.result} />
                <div className="actions">
                  <Link to={`/learn/${quiz.course_id}`} className="btn btn-primary">Back to course</Link>
                  {canAttempt && <Button variant="outline" onClick={begin}>Try again</Button>}
                  {outcome.progress?.is_completed && (
                    <Link to="/dashboard?tab=certificates" className="btn btn-accent"><FiAward aria-hidden="true" /> View certificate</Link>
                  )}
                </div>
              </>
            )}

            {!outcome && preview && (
              questions.map((q, n) => (
                <div key={q.id} className="panel question">
                  <h3>{n + 1}. {q.prompt}</h3>
                  <ul className="review-options">{q.options.map((o) => <li key={o}><span>{o}</span></li>)}</ul>
                </div>
              ))
            )}

            {!outcome && !preview && !started && (
              <div className="panel">
                {!questions.length ? <EmptyState title="This quiz has no questions yet" />
                  : canAttempt ? <Button onClick={begin}>{attempts.length ? "Try again" : "Start quiz"}</Button>
                    : <Alert>You have used all attempts for this quiz.</Alert>}
              </div>
            )}

            {!outcome && started && (
              <form onSubmit={submit} noValidate>
                {questions.map((q, number) => (
                  <fieldset key={q.id} id={`question-${q.id}`}
                    className={`panel question ${error && answers[q.id] === undefined ? "missing" : ""}`}>
                    <legend>{number + 1}. {q.prompt}</legend>
                    {q.options.map((option, i) => (
                      <label key={i} className={`option ${answers[q.id] === i ? "selected" : ""}`}>
                        <input type="radio" name={`q${q.id}`} checked={answers[q.id] === i}
                          onChange={() => setAnswers({ ...answers, [q.id]: i })} />
                        <span>{option}</span>
                      </label>
                    ))}
                  </fieldset>
                ))}
                <Alert type="error">{error}</Alert>
                <div className="actions between sticky-actions">
                  <span>{answered} of {questions.length} answered</span>
                  <Button type="submit" busy={busy}>Submit answers</Button>
                </div>
              </form>
            )}

            {!started && !preview && attempts.length > 0 && (
              <section className="panel">
                <h2>Your attempts</h2>
                <Table rows={attempts} columns={[
                  ["Date", (a) => formatDateTime(a.submitted_at)],
                  ["Score", (a) => `${a.percentage}% (${a.score}/${a.total})`],
                  ["Result", (a) => <Badge tone={a.passed ? "success" : "danger"}>{a.passed ? "Passed" : "Failed"}</Badge>],
                  ["Review", (a) => <Link to={`/results/${a.id}`}>View answers</Link>],
                ]} />
              </section>
            )}
          </div>
        );
      }}
    </Loadable>
  );
}

export function QuizResult({ params }) {
  const state = useApi(`/quiz-results/${encodeURIComponent(params.id)}`);
  useTitle("Quiz result");
  return (
    <Loadable state={state}>
      {({ result }) => (
        <div className="container section narrow">
          <p className="crumbs"><Link to={`/quizzes/${result.quiz_id}`}>{result.quiz_title}</Link> / Attempt on {formatDateTime(result.submitted_at)}</p>
          <h1>Quiz result</h1>
          <ResultView result={result} />
        </div>
      )}
    </Loadable>
  );
}
