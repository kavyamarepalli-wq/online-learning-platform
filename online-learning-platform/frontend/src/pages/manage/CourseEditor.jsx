// Create or edit a course. Tabs cover details, lessons, materials, quizzes and students.
import { useState } from "react";
import { Thumbnail } from "../../components/CourseCard.jsx";
import { Alert, Badge, Button, Field, Loadable, Tabs, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { useAuth } from "../../lib/auth.jsx";
import { checks } from "../../lib/format.js";
import { useApi, useForm, useTitle } from "../../lib/hooks.js";
import { Link, navigate, useQuery } from "../../lib/router.jsx";
import CourseStudents from "./CourseStudents.jsx";
import { PendingApproval } from "./InstructorDashboard.jsx";
import LessonsPanel from "./LessonsPanel.jsx";
import MaterialsPanel from "./MaterialsPanel.jsx";
import QuizzesPanel from "./QuizzesPanel.jsx";

const EMPTY = { title: "", summary: "", description: "", category: "", level: "Beginner", status: "draft", is_featured: false };

function DetailsForm({ course, onSaved }) {
  const { user } = useAuth();
  const toast = useToast();
  const meta = useApi("/meta");
  const instructors = useApi(user.role === "admin" ? "/manage/instructors" : null);
  const form = useForm(
    course ? { ...EMPTY, ...course } : EMPTY,
    (v) => ({
      title: checks.min(v.title, 3, "Title"),
      summary: checks.min(v.summary, 10, "Short summary"),
      description: checks.min(v.description, 20, "Description"),
      category: v.category ? "" : "Choose a category.",
      instructor_id: user.role === "admin" && !v.instructor_id ? "Choose an instructor." : "",
    }));

  const submit = form.submit(async (v) => {
    const body = {
      title: v.title, summary: v.summary, description: v.description, category: v.category,
      level: v.level, status: v.status,
      ...(user.role === "admin" && { instructor_id: Number(v.instructor_id), is_featured: v.is_featured }),
    };
    if (course) {
      await api.put(`/manage/courses/${course.id}`, body);
      toast.success("Course saved.");
      onSaved();
    } else {
      const reply = await api.post("/manage/courses", body);
      toast.success("Course created. Now add lessons, then publish it.");
      navigate(`/manage/courses/${reply.course.id}?tab=lessons`, { replace: true });
    }
  });

  const options = instructors.data?.items || [];
  // An instructor who is no longer approved still shows as the current owner.
  const missingOwner = course && instructors.data && !options.some((i) => i.id === course.instructor_id);

  return (
    <form className="panel" onSubmit={submit} noValidate>
      <Alert type="error">{form.message}</Alert>
      <Field label="Course title" maxLength={150} {...form.bind("title")} />
      <Field label="Short summary" maxLength={300} hint="Shown on course cards." {...form.bind("summary")} />
      <Field label="Description" as="textarea" rows={6} maxLength={10000} {...form.bind("description")} />
      <div className="form-row">
        <Field label="Category" as="select" {...form.bind("category")}>
          <option value="">Choose...</option>
          {meta.data?.categories.map((c) => <option key={c}>{c}</option>)}
        </Field>
        <Field label="Level" as="select" {...form.bind("level")}>
          {(meta.data?.levels || [form.values.level]).map((l) => <option key={l}>{l}</option>)}
        </Field>
        <Field label="Status" as="select" {...form.bind("status")}
          hint={course ? "Published courses appear in the catalogue." : "Publish after adding a lesson."}>
          <option value="draft">Draft</option>
          <option value="published" disabled={!course}>Published</option>
        </Field>
      </div>
      {user.role === "admin" && (
        <>
          <Field label="Instructor" as="select" {...form.bind("instructor_id")}>
            <option value="">Choose...</option>
            {missingOwner && <option value={course.instructor_id}>{course.instructor.name}</option>}
            {options.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </Field>
          <label className="checkbox">
            <input type="checkbox" checked={form.values.is_featured}
              onChange={(e) => form.set("is_featured", e.target.checked)} />
            Feature this course on the home page
          </label>
        </>
      )}
      <Button type="submit" busy={form.busy}>{course ? "Save changes" : "Create course"}</Button>
    </form>
  );
}

function CoverUpload({ course, onSaved }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const upload = async (event) => {
    const file = event.target.files[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) return setError("The image must be 5 MB or smaller.");
    const data = new FormData();
    data.append("file", file);
    setBusy(true);
    setError("");
    try {
      await api.upload(`/manage/courses/${course.id}/thumbnail`, data);
      toast.success("Cover image updated.");
      onSaved();
    } catch (problem) {
      setError(problem.message);
    }
    setBusy(false);
  };
  return (
    <div className="panel cover-upload">
      <Thumbnail src={course.thumbnail_url} title={course.title} />
      <Field label="Cover image" type="file" accept=".png,.jpg,.jpeg,.webp" onChange={upload}
        disabled={busy} error={error} hint={busy ? "Uploading..." : "PNG, JPG or WebP, 16:9 looks best, up to 5 MB."} />
    </div>
  );
}

export default function CourseEditor({ params }) {
  const { user } = useAuth();
  const isNew = !params.id;
  const state = useApi(isNew ? null : `/manage/courses/${encodeURIComponent(params.id)}`);
  const tab = useQuery().get("tab") || "details";
  const back = user.role === "admin" ? "/admin?tab=courses" : "/instructor";
  useTitle(isNew ? "New course" : state.data?.course.title || "Manage course");

  if (user.role === "instructor" && !user.is_approved) {
    return <div className="container section"><PendingApproval /></div>;
  }
  return (
    <div className="container section">
      <p className="crumbs"><Link to={back}>{user.role === "admin" ? "Admin dashboard" : "Instructor studio"}</Link> / {isNew ? "New course" : "Manage course"}</p>
      {isNew ? (
        <>
          <h1>Create a course</h1>
          <DetailsForm />
        </>
      ) : (
        <Loadable state={state}>
          {({ course, lessons, materials, quizzes }) => (
            <>
              <div className="lesson-head">
                <h1>{course.title}</h1>
                <Badge tone={course.status === "published" ? "success" : "warning"}>{course.status}</Badge>
              </div>
              <Tabs active={tab}
                onChange={(t) => navigate(`/manage/courses/${course.id}?tab=${t}`, { replace: true, scroll: false })}
                tabs={[["details", "Details"], ["lessons", `Lessons (${lessons.length})`],
                  ["materials", `Materials (${materials.length})`], ["quizzes", `Quizzes (${quizzes.length})`],
                  ["students", "Students and results"]]} />
              {tab === "details" && (
                <div className="split">
                  <DetailsForm key={course.updated_at} course={course} onSaved={state.reload} />
                  <CoverUpload course={course} onSaved={state.reload} />
                </div>
              )}
              {tab === "lessons" && <LessonsPanel course={course} lessons={lessons} reload={state.reload} />}
              {tab === "materials" && <MaterialsPanel course={course} materials={materials} lessons={lessons} reload={state.reload} />}
              {tab === "quizzes" && <QuizzesPanel course={course} quizzes={quizzes} reload={state.reload} />}
              {tab === "students" && <CourseStudents course={course} />}
            </>
          )}
        </Loadable>
      )}
    </div>
  );
}
