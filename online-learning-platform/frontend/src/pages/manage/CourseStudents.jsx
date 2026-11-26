import { Badge, Loadable, ProgressBar, Table } from "../../components/ui.jsx";
import { formatDate, formatDateTime } from "../../lib/format.js";
import { useApi } from "../../lib/hooks.js";
import { Link } from "../../lib/router.jsx";

export default function CourseStudents({ course }) {
  const students = useApi(`/manage/courses/${course.id}/students`);
  const results = useApi(`/manage/courses/${course.id}/results`);
  return (
    <>
      <section className="panel">
        <h2>Student progress</h2>
        <Loadable state={students}>
          {({ items }) => (
            <Table rows={items} rowKey="enrollment_id" empty="No students have enrolled yet." columns={[
              ["Student", (s) => <><strong>{s.student_name}</strong><small className="block">{s.student_email}</small></>],
              ["Progress", (s) => <ProgressBar value={s.percentage} label={s.student_name} />],
              ["Lessons", (s) => `${s.completed_lessons}/${s.total_lessons}`],
              ["Quizzes", (s) => `${s.passed_quizzes}/${s.total_quizzes}`],
              ["Enrolled", (s) => formatDate(s.enrolled_at)],
              ["Status", (s) => <Badge tone={s.is_completed ? "success" : "neutral"}>{s.is_completed ? "Completed" : "In progress"}</Badge>],
            ]} />
          )}
        </Loadable>
      </section>
      <section className="panel">
        <h2>Quiz results</h2>
        <Loadable state={results}>
          {({ items }) => (
            <Table rows={items} empty="No quiz attempts yet." columns={[
              ["Student", (r) => <><strong>{r.student_name}</strong><small className="block">{r.student_email}</small></>],
              ["Quiz", (r) => <Link to={`/results/${r.id}`}>{r.quiz_title}</Link>],
              ["Score", (r) => `${r.percentage}% (${r.score}/${r.total})`],
              ["Result", (r) => <Badge tone={r.passed ? "success" : "danger"}>{r.passed ? "Passed" : "Failed"}</Badge>],
              ["Date", (r) => formatDateTime(r.submitted_at)],
            ]} />
          )}
        </Loadable>
      </section>
    </>
  );
}
