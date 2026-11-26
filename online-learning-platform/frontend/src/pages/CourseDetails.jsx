import { useState } from "react";
import { FiBookOpen, FiCheckSquare, FiClock, FiDownload, FiEdit, FiFileText, FiLock, FiPlayCircle, FiUsers } from "react-icons/fi";
import { Thumbnail } from "../components/CourseCard.jsx";
import { Alert, Badge, Button, Loadable, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { useAuth } from "../lib/auth.jsx";
import { formatDuration, formatSize, plural } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { Link, navigate } from "../lib/router.jsx";

function EnrollBox({ data }) {
  const { user } = useAuth();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const { course, is_enrolled: enrolled, can_manage: manager } = data;

  const enroll = async () => {
    setBusy(true);
    try {
      await api.post(`/courses/${course.id}/enroll`);
      toast.success("You are enrolled. Happy learning!");
      navigate(`/learn/${course.id}`);
    } catch (error) {
      toast.error(error.message);
      setBusy(false);
    }
  };

  if (enrolled) {
    return <Link to={`/learn/${course.id}`} className="btn btn-primary btn-block">Continue learning</Link>;
  }
  if (manager) {
    return (
      <>
        <Link to={`/manage/courses/${course.id}`} className="btn btn-primary btn-block"><FiEdit aria-hidden="true" /> Edit course</Link>
        <Link to={`/learn/${course.id}`} className="btn btn-outline btn-block">Preview as a student</Link>
      </>
    );
  }
  if (!user) {
    return (
      <>
        <Link to={`/login?next=/courses/${course.id}`} className="btn btn-primary btn-block">Log in to enroll</Link>
        <Link to={`/register?next=/courses/${course.id}`} className="btn btn-outline btn-block">Create an account</Link>
      </>
    );
  }
  if (user.role !== "student") return <Alert>Only student accounts can enroll in courses.</Alert>;
  return <Button className="btn-block" busy={busy} onClick={enroll}>Enroll for free</Button>;
}

export default function CourseDetails({ params }) {
  const state = useApi(`/courses/${encodeURIComponent(params.id)}`);
  useTitle(state.data?.course.title || "Course");

  return (
    <Loadable state={state}>
      {(data) => {
        const { course, lessons, materials, quizzes } = data;
        return (
          <>
            <section className="course-hero">
              <div className="container">
                <div className="badges">
                  <Badge tone="primary">{course.category}</Badge>
                  <Badge>{course.level}</Badge>
                  {course.status === "draft" && <Badge tone="warning">Draft</Badge>}
                </div>
                <h1>{course.title}</h1>
                <p>{course.summary}</p>
                <p className="hero-meta">
                  <span><FiBookOpen aria-hidden="true" /> {plural(course.lesson_count, "lesson")}</span>
                  {course.duration_seconds > 0 && <span><FiClock aria-hidden="true" /> {formatDuration(course.duration_seconds)}</span>}
                  <span><FiCheckSquare aria-hidden="true" /> {plural(course.quiz_count, "quiz", "quizzes")}</span>
                  <span><FiUsers aria-hidden="true" /> {plural(course.student_count, "student")}</span>
                </p>
              </div>
            </section>

            <div className="container section split">
              <div>
                <section className="panel">
                  <h2>About this course</h2>
                  <p className="pre">{course.description}</p>
                </section>
                <section className="panel">
                  <h2>Course content</h2>
                  {!data.is_enrolled && !data.can_manage && (
                    <p className="meta"><FiLock aria-hidden="true" /> Enroll to watch lessons, download materials and take quizzes.</p>
                  )}
                  <ul className="outline-list">
                    {lessons.map((lesson, index) => (
                      <li key={lesson.id}>
                        {lesson.video_type === "none" ? <FiFileText aria-hidden="true" /> : <FiPlayCircle aria-hidden="true" />}
                        <span>{index + 1}. {lesson.title}</span>
                        <small>{formatDuration(lesson.duration_seconds)}</small>
                      </li>
                    ))}
                    {quizzes.map((quiz) => (
                      <li key={`q${quiz.id}`}>
                        <FiCheckSquare aria-hidden="true" />
                        <span>{quiz.title}</span>
                        <small>{plural(quiz.question_count, "question")}</small>
                      </li>
                    ))}
                  </ul>
                  {!lessons.length && <p>Lessons are being prepared.</p>}
                </section>
                {materials.length > 0 && (
                  <section className="panel">
                    <h2>Study materials</h2>
                    <ul className="outline-list">
                      {materials.map((m) => (
                        <li key={m.id}>
                          <FiDownload aria-hidden="true" />
                          <span>{m.title}</span>
                          <small>{formatSize(m.file_size)}</small>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
                <section className="panel instructor">
                  <h2>Your instructor</h2>
                  <div className="avatar" aria-hidden="true">{course.instructor.name.slice(0, 1)}</div>
                  <div>
                    <h3>{course.instructor.name}</h3>
                    <p className="meta">{course.instructor.headline}</p>
                    {course.instructor.bio && <p>{course.instructor.bio}</p>}
                    {course.instructor.expertise && <p className="meta">Expertise: {course.instructor.expertise}</p>}
                  </div>
                </section>
              </div>
              <aside className="panel enroll-box">
                <Thumbnail src={course.thumbnail_url} title={course.title} />
                <EnrollBox data={data} />
                <ul className="check-list">
                  <li>Video lessons and notes</li>
                  <li>Downloadable study materials</li>
                  <li>Quizzes with instant scores</li>
                  <li>Certificate on completion</li>
                </ul>
              </aside>
            </div>
          </>
        );
      }}
    </Loadable>
  );
}
