import { useState } from "react";
import { FiEdit, FiPlus, FiTrash2, FiX } from "react-icons/fi";
import { Alert, Button, EmptyState, Field, Modal, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { checks, plural } from "../../lib/format.js";
import { useForm } from "../../lib/hooks.js";

let nextKey = 0;
const blank = () => ({ key: ++nextKey, prompt: "", options: ["", ""], correct_index: null, explanation: "" });

function validate(v) {
  const errors = { title: checks.min(v.title, 3, "Quiz title") };
  if (!(v.pass_percentage >= 1 && v.pass_percentage <= 100)) errors.pass_percentage = "Enter 1 to 100.";
  if (!(v.max_attempts >= 0 && v.max_attempts <= 100) || v.max_attempts === "") errors.max_attempts = "Enter 0 to 100.";
  v.questions.forEach((q, i) => {
    const options = q.options.map((o) => o.trim());
    if (q.prompt.trim().length < 3) errors[`questions.${i}.prompt`] = "Write the question (at least 3 characters).";
    if (options.some((o) => !o)) errors[`questions.${i}.options`] = "Fill in every option or remove it.";
    else if (new Set(options).size !== options.length) errors[`questions.${i}.options`] = "Options must be different.";
    if (q.correct_index === null) errors[`questions.${i}.correct_index`] = "Select the correct option.";
  });
  return errors;
}

function QuizForm({ course, quiz, onDone, onClose }) {
  const form = useForm(
    quiz
      ? { ...quiz, questions: quiz.questions.map((q) => ({ ...q, key: ++nextKey })) }
      : { title: "", description: "", pass_percentage: 60, max_attempts: 0, questions: [blank()] },
    validate);
  const { questions } = form.values;

  // Server messages are numbered by position, so they are cleared after any change.
  const [dirtyErrors, setDirtyErrors] = useState(false);
  const errors = dirtyErrors ? {} : form.errors;
  const setQuestions = (list) => { setDirtyErrors(true); form.set("questions", list); };
  const patch = (index, changes) => setQuestions(questions.map((q, i) => (i === index ? { ...q, ...changes } : q)));

  const submit = (event) => {
    setDirtyErrors(false);
    return form.submit(async (v) => {
      const body = {
        title: v.title, description: v.description,
        pass_percentage: Number(v.pass_percentage), max_attempts: Number(v.max_attempts),
        questions: v.questions.map(({ prompt, options, correct_index, explanation }) =>
          ({ prompt, options, correct_index, explanation })),
      };
      if (quiz) await api.put(`/manage/quizzes/${quiz.id}`, body);
      else await api.post(`/manage/courses/${course.id}/quizzes`, body);
      onDone();
    })(event);
  };

  return (
    <Modal title={quiz ? "Edit quiz" : "New quiz"} onClose={() => !form.busy && onClose()} wide>
      <form onSubmit={submit} noValidate>
        <Field label="Quiz title" maxLength={150} {...form.bind("title")} />
        <Field label="Instructions (optional)" maxLength={1000} {...form.bind("description")} />
        <div className="form-row">
          <Field label="Pass mark (%)" type="number" min={1} max={100} {...form.bind("pass_percentage")} />
          <Field label="Maximum attempts" type="number" min={0} max={100} hint="0 means unlimited." {...form.bind("max_attempts")} />
        </div>
        {questions.map((q, i) => (
          <fieldset key={q.key} className="panel question builder">
            <legend>Question {i + 1}</legend>
            <Field label="Question" maxLength={1000} value={q.prompt} error={errors[`questions.${i}.prompt`]}
              onChange={(e) => patch(i, { prompt: e.target.value })} />
            <p className="hint">Select the circle next to the correct answer.</p>
            {q.options.map((option, o) => (
              <div key={o} className="option-edit">
                <input type="radio" name={`correct-${q.key}`} checked={q.correct_index === o}
                  aria-label={`Option ${o + 1} is correct`} onChange={() => patch(i, { correct_index: o })} />
                <input type="text" value={option} maxLength={300} placeholder={`Option ${o + 1}`}
                  aria-label={`Question ${i + 1}, option ${o + 1}`}
                  onChange={(e) => patch(i, { options: q.options.map((x, n) => (n === o ? e.target.value : x)) })} />
                <button type="button" className="icon-btn" disabled={q.options.length <= 2} aria-label={`Remove option ${o + 1}`}
                  onClick={() => patch(i, {
                    options: q.options.filter((_, n) => n !== o),
                    correct_index: q.correct_index === o ? null
                      : q.correct_index > o ? q.correct_index - 1 : q.correct_index,
                  })}><FiX /></button>
              </div>
            ))}
            {["options", "correct_index"].map((name) => errors[`questions.${i}.${name}`] && (
              <p key={name} className="error-text">{errors[`questions.${i}.${name}`]}</p>
            ))}
            <Field label="Explanation (optional)" maxLength={1000} value={q.explanation}
              onChange={(e) => patch(i, { explanation: e.target.value })} />
            <div className="actions between">
              <Button variant="link" disabled={q.options.length >= 6} onClick={() => patch(i, { options: [...q.options, ""] })}>
                <FiPlus aria-hidden="true" /> Add option
              </Button>
              <Button variant="link" className="danger-text" disabled={questions.length <= 1}
                onClick={() => setQuestions(questions.filter((_, n) => n !== i))}>
                <FiTrash2 aria-hidden="true" /> Remove question
              </Button>
            </div>
          </fieldset>
        ))}
        <Button variant="outline" onClick={() => setQuestions([...questions, blank()])} disabled={questions.length >= 100}>
          <FiPlus aria-hidden="true" /> Add question
        </Button>
        <Alert type="error">{form.message}</Alert>
        <div className="actions end">
          <Button variant="outline" onClick={onClose} disabled={form.busy}>Cancel</Button>
          <Button type="submit" busy={form.busy}>Save quiz</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function QuizzesPanel({ course, quizzes, reload }) {
  const toast = useToast();
  const [editing, setEditing] = useState(undefined);
  const remove = async (quiz) => {
    const sure = await toast.confirm({
      title: "Delete quiz?", danger: true, action: "Delete",
      text: `"${quiz.title}" and all student results for it will be deleted.`,
    });
    if (!sure) return;
    try {
      await api.delete(`/manage/quizzes/${quiz.id}`);
      toast.success("Quiz deleted.");
      reload();
    } catch (error) {
      toast.error(error.message);
    }
  };
  return (
    <section className="panel">
      <div className="section-head">
        <h2>Quizzes</h2>
        <Button onClick={() => setEditing(null)}><FiPlus aria-hidden="true" /> Add quiz</Button>
      </div>
      {!quizzes.length && <EmptyState title="No quizzes yet" text="Add multiple-choice questions to check understanding." />}
      <ul className="manage-list">
        {quizzes.map((quiz) => (
          <li key={quiz.id}>
            <div className="grow">
              <strong>{quiz.title}</strong>
              <small className="block">{plural(quiz.questions.length, "question")} · pass mark {quiz.pass_percentage}% ·{" "}
                {quiz.max_attempts ? plural(quiz.max_attempts, "attempt") : "unlimited attempts"}</small>
            </div>
            <div className="row-actions">
              <Button variant="outline" size="sm" onClick={() => setEditing(quiz)}><FiEdit aria-hidden="true" /> Edit</Button>
              <Button variant="danger" size="sm" onClick={() => remove(quiz)} aria-label={`Delete ${quiz.title}`}><FiTrash2 /></Button>
            </div>
          </li>
        ))}
      </ul>
      {editing !== undefined && (
        <QuizForm course={course} quiz={editing} onClose={() => setEditing(undefined)}
          onDone={() => { setEditing(undefined); toast.success("Quiz saved."); reload(); }} />
      )}
    </section>
  );
}
