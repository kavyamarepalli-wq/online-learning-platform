// The course list used by both the instructor studio and the admin dashboard.
import { FiEdit, FiEye, FiPlus, FiTrash2 } from "react-icons/fi";
import { Badge, Button, Loadable, Table, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { formatDate } from "../../lib/format.js";
import { useApi } from "../../lib/hooks.js";
import { Link } from "../../lib/router.jsx";

export default function CourseTable({ showInstructor = false }) {
  const state = useApi("/manage/courses");
  const toast = useToast();

  const remove = async (course) => {
    const sure = await toast.confirm({
      title: "Delete course?", danger: true, action: "Delete",
      text: `"${course.title}" with its lessons, files, quizzes and enrollments will be permanently deleted. Issued certificates stay valid.`,
    });
    if (!sure) return;
    try {
      await api.delete(`/manage/courses/${course.id}`);
      toast.success("Course deleted.");
      state.reload();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const columns = [
    ["Course", (c) => <><strong>{c.title}</strong><small className="block">{c.category} · {c.level}{c.is_featured ? " · Featured" : ""}</small></>],
    ...(showInstructor ? [["Instructor", (c) => c.instructor.name]] : []),
    ["Status", (c) => <Badge tone={c.status === "published" ? "success" : "warning"}>{c.status}</Badge>],
    ["Content", (c) => `${c.lesson_count} lessons · ${c.quiz_count} quizzes`],
    ["Students", (c) => c.student_count],
    ["Updated", (c) => formatDate(c.updated_at)],
    ["Actions", (c) => (
      <div className="row-actions">
        <Link to={`/manage/courses/${c.id}`} className="btn btn-outline btn-sm"><FiEdit aria-hidden="true" /> Manage</Link>
        <Link to={`/courses/${c.id}`} className="btn btn-outline btn-sm"><FiEye aria-hidden="true" /> View</Link>
        <Button variant="danger" size="sm" onClick={() => remove(c)} aria-label={`Delete ${c.title}`}><FiTrash2 /></Button>
      </div>
    )],
  ];

  return (
    <>
      <div className="section-head">
        <h2>{showInstructor ? "All courses" : "My courses"}</h2>
        <Link to="/manage/courses/new" className="btn btn-primary"><FiPlus aria-hidden="true" /> New course</Link>
      </div>
      <Loadable state={state}>
        {({ items }) => <Table rows={items} columns={columns} empty="No courses yet. Create the first one." />}
      </Loadable>
    </>
  );
}
