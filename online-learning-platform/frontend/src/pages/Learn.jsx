// The study screen: video player, lesson notes, materials, quizzes and progress.
import { useEffect, useRef, useState } from "react";
import { FiAward, FiCheck, FiCheckCircle, FiCheckSquare, FiCircle, FiDownload, FiLogOut, FiPlayCircle } from "react-icons/fi";
import { Alert, Badge, Button, EmptyState, Loadable, ProgressBar, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { formatDuration, formatSize, plural } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { Link, navigate, useQuery } from "../lib/router.jsx";

const SAVE_EVERY = 10; // seconds of playback between automatic saves

function VideoPlayer({ lesson, onSave }) {
  const [failed, setFailed] = useState(false);
  const video = useRef(null);
  // The first address is kept, so saving progress never restarts the video.
  const [source] = useState(lesson.video_url);
  const track = useRef({
    watched: lesson.watched_seconds, previous: null, saved: lesson.watched_seconds,
    position: lesson.last_position, dirty: false,
  });
  const save = useRef(onSave);
  save.current = onSave;

  const flush = (options) => {
    const t = track.current;
    if (!t.dirty) return;
    t.dirty = false;
    t.saved = t.watched;
    save.current({ position: Math.floor(t.position), watched_seconds: Math.round(t.watched) }, options);
  };

  useEffect(() => {
    const leave = () => flush({ keepalive: true });
    window.addEventListener("pagehide", leave);
    return () => { window.removeEventListener("pagehide", leave); flush(); };
  }, []);

  const loaded = () => {
    const { duration } = video.current;
    const resume = lesson.last_position;
    if (resume > 0 && resume < duration - 3) video.current.currentTime = resume;
  };

  // Only time that actually played counts; jumping ahead does not.
  const tick = () => {
    const t = track.current;
    const time = video.current.currentTime;
    const step = t.previous === null ? 0 : time - t.previous;
    t.previous = time;
    if (video.current.paused && !video.current.ended) return;
    if (step > 0 && step < 1.5 * Math.max(video.current.playbackRate, 1)) {
      t.watched += step;
      t.position = time;
      t.dirty = true;
      if (t.watched - t.saved >= SAVE_EVERY) flush();
    }
  };

  const ended = () => {
    const t = track.current;
    // Rounding can leave a fully watched short video just under its length.
    t.position = 0;
    t.dirty = true;
    flush();
  };

  if (failed) {
    return (
      <div className="video-fallback">
        <p>The video could not be played. The link may have expired.</p>
        <Button variant="outline" onClick={() => window.location.reload()}>Reload page</Button>
      </div>
    );
  }
  return (
    <video ref={video} className="video" src={source} controls playsInline preload="metadata"
      onLoadedMetadata={loaded} onTimeUpdate={tick} onPause={() => flush()} onEnded={ended}
      onSeeking={() => { track.current.previous = null; }}
      onSeeked={() => { track.current.position = video.current.currentTime; track.current.dirty = true; }}
      onError={() => setFailed(true)} />
  );
}

function Player({ lesson, onSave }) {
  if (lesson.video_type === "youtube") {
    return (
      <iframe className="video" src={lesson.video_url} title={lesson.title} allowFullScreen
        allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
        referrerPolicy="strict-origin-when-cross-origin" />
    );
  }
  if (lesson.video_type === "none") return null;
  return <VideoPlayer lesson={lesson} onSave={onSave} />;
}

function LearnView({ state }) {
  const query = useQuery();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const { course, lessons, materials, quizzes, progress, preview } = state.data;
  const wanted = Number(query.get("lesson"));
  const lesson = lessons.find((l) => l.id === wanted)
    || lessons.find((l) => !l.is_completed) || lessons[0];
  const index = lessons.indexOf(lesson);
  const open = (id) => navigate(`/learn/${course.id}?lesson=${id}`, { scroll: false, replace: true });

  // Put the lesson in the address, so it stays selected after it is completed.
  useEffect(() => {
    if (lesson && wanted !== lesson.id) open(lesson.id);
  }, [lesson?.id, wanted]);

  const save = async (lessonId, body, options) => {
    if (preview) return null;
    try {
      const reply = await api.put(`/lessons/${lessonId}/progress`, body, options);
      const justFinished = reply.progress.is_completed && !progress?.is_completed;
      state.setData((old) => old && {
        ...old,
        progress: reply.progress,
        lessons: old.lessons.map((l) => (l.id === lessonId ? { ...l, ...reply.lesson } : l)),
      });
      if (justFinished) toast.success("Course completed! Your certificate is ready.");
      return reply;
    } catch (error) {
      toast.error(`Progress was not saved. ${error.message}`);
      return null;
    }
  };

  const toggle = async () => {
    setBusy(true);
    await save(lesson.id, { completed: !lesson.is_completed });
    setBusy(false);
  };

  const leave = async () => {
    const sure = await toast.confirm({
      title: "Leave this course?", danger: true, action: "Leave course",
      text: "Your lesson progress will be removed. Quiz scores and certificates are kept.",
    });
    if (!sure) return;
    try {
      await api.delete(`/courses/${course.id}/enroll`);
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="container section">
      <p className="crumbs"><Link to={preview ? `/courses/${course.id}` : "/dashboard"}>
        {preview ? "Course page" : "My learning"}</Link> / {course.title}</p>
      {preview && <Alert>Preview mode: progress is not recorded.</Alert>}
      {progress && (
        <div className="panel progress-panel">
          <div className="grow">
            <h2>Your progress</h2>
            <ProgressBar value={progress.percentage} />
            <p className="meta">
              {progress.completed_lessons} of {plural(progress.total_lessons, "lesson")} completed,{" "}
              {progress.passed_quizzes} of {plural(progress.total_quizzes, "quiz", "quizzes")} passed
            </p>
          </div>
          {progress.certificate_id && (
            <Button variant="accent" onClick={() => api.download(
              `/certificates/${progress.certificate_id}/download`, "certificate.pdf")
              .catch((e) => toast.error(e.message))}>
              <FiAward aria-hidden="true" /> Download certificate
            </Button>
          )}
        </div>
      )}

      <div className="learn-layout">
        <div>
          {lesson ? (
            <article className="panel lesson-view">
              <Player key={lesson.id} lesson={lesson}
                onSave={(body, options) => save(lesson.id, body, options)} />
              <div className="lesson-head">
                <h1>{lesson.title}</h1>
                {lesson.is_completed && <Badge tone="success">Completed</Badge>}
              </div>
              {lesson.content && <p className="pre">{lesson.content}</p>}
              {!preview && (
                <p className="meta">
                  {lesson.video_type === "none" || lesson.video_type === "youtube" || !lesson.duration_seconds
                    ? "Mark the lesson as complete when you have finished it."
                    : "The lesson completes automatically after you watch 90% of the video."}
                </p>
              )}
              <div className="actions between">
                <Button variant="outline" disabled={index <= 0} onClick={() => open(lessons[index - 1].id)}>Previous</Button>
                {!preview && (
                  <Button variant={lesson.is_completed ? "outline" : "success"} busy={busy} onClick={toggle}>
                    <FiCheck aria-hidden="true" /> {lesson.is_completed ? "Mark as not completed" : "Mark as complete"}
                  </Button>
                )}
                <Button disabled={index >= lessons.length - 1} onClick={() => open(lessons[index + 1].id)}>Next lesson</Button>
              </div>
            </article>
          ) : <EmptyState title="No lessons yet" text="The instructor has not added lessons to this course." />}

          <section className="panel">
            <h2>Study materials</h2>
            {materials.length ? (
              <ul className="outline-list">
                {materials.map((m) => (
                  <li key={m.id}>
                    <FiDownload aria-hidden="true" />
                    <span>{m.title}<small className="block">{m.file_name} · {formatSize(m.file_size)}
                      {m.lesson_id ? ` · ${lessons.find((l) => l.id === m.lesson_id)?.title ?? ""}` : ""}</small></span>
                    <a className="btn btn-outline btn-sm" href={m.download_url} download={m.file_name}>Download</a>
                  </li>
                ))}
              </ul>
            ) : <p className="meta">No study materials for this course yet.</p>}
          </section>
        </div>

        <aside>
          <section className="panel">
            <h2>Lessons</h2>
            <ol className="lesson-list">
              {lessons.map((item, i) => (
                <li key={item.id}>
                  <button type="button" onClick={() => open(item.id)}
                    aria-current={item.id === lesson?.id ? "true" : undefined}>
                    {item.is_completed ? <FiCheckCircle className="done-icon" aria-label="Completed" />
                      : item.id === lesson?.id ? <FiPlayCircle aria-hidden="true" /> : <FiCircle aria-hidden="true" />}
                    <span>{i + 1}. {item.title}</span>
                    <small>{formatDuration(item.duration_seconds)}</small>
                  </button>
                </li>
              ))}
            </ol>
          </section>
          <section className="panel">
            <h2>Quizzes</h2>
            {quizzes.length ? quizzes.map((quiz) => (
              <div key={quiz.id} className="quiz-row">
                <FiCheckSquare aria-hidden="true" />
                <div className="grow">
                  <strong>{quiz.title}</strong>
                  <small className="block">
                    {plural(quiz.question_count, "question")} · pass mark {quiz.pass_percentage}%
                    {quiz.best_percentage !== null ? ` · best ${quiz.best_percentage}%` : ""}
                  </small>
                  {quiz.passed && <Badge tone="success">Passed</Badge>}
                </div>
                {quiz.question_count > 0 && (
                  <Link to={`/quizzes/${quiz.id}`} className="btn btn-primary btn-sm">
                    {preview ? "View" : quiz.attempts_used ? "Open" : "Start"}
                  </Link>
                )}
              </div>
            )) : <p className="meta">This course has no quizzes.</p>}
          </section>
          {!preview && (
            <Button variant="link" className="danger-text" onClick={leave}>
              <FiLogOut aria-hidden="true" /> Leave course
            </Button>
          )}
        </aside>
      </div>
    </div>
  );
}

export default function Learn({ params }) {
  const state = useApi(`/courses/${encodeURIComponent(params.id)}/learn`);
  useTitle(state.data?.course.title || "Learn");
  return <Loadable state={state}>{() => <LearnView state={state} />}</Loadable>;
}
