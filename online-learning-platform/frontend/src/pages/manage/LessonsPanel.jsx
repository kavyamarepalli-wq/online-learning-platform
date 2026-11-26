import { useState } from "react";
import { FiArrowDown, FiArrowUp, FiEdit, FiPlus, FiTrash2 } from "react-icons/fi";
import { Alert, Button, EmptyState, Field, Modal, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { checks, formatDuration } from "../../lib/format.js";
import { useForm } from "../../lib/hooks.js";

const SOURCES = { upload: "Uploaded video", youtube: "YouTube video", url: "Video link", none: "Reading lesson" };

// Reads the length of a video in the browser, so completion can be tracked.
function videoDuration(source) {
  return new Promise((resolve) => {
    const video = document.createElement("video");
    const finish = (value) => { clearTimeout(timer); video.removeAttribute("src"); resolve(value); };
    const timer = setTimeout(() => finish(0), 8000);
    video.preload = "metadata";
    video.onloadedmetadata = () => finish(Number.isFinite(video.duration) ? Math.round(video.duration) : 0);
    video.onerror = () => finish(0);
    video.src = source;
  });
}

function LessonForm({ course, lesson, onDone, onClose }) {
  const [file, setFile] = useState(null);
  const [percent, setPercent] = useState(null);
  const hasUpload = lesson?.video_type === "upload";
  const form = useForm(
    {
      title: lesson?.title || "", content: lesson?.content || "",
      video_type: lesson?.video_type || "upload",
      video_url: (lesson?.video_type !== "upload" && lesson?.video_url) || "",
      duration_seconds: lesson?.duration_seconds || "",
    },
    (v) => ({
      title: checks.min(v.title, 3, "Lesson title"),
      video: v.video_type === "upload" && !file && !hasUpload ? "Choose a video file." : "",
      video_url: ["youtube", "url"].includes(v.video_type) && !v.video_url.trim() ? "Enter the video link." : "",
      content: v.video_type === "none" && !v.content.trim() ? "A reading lesson needs notes." : "",
    }));
  const type = form.values.video_type;

  const chooseFile = async (event) => {
    const chosen = event.target.files[0] || null;
    setFile(chosen);
    if (!chosen) return;
    const url = URL.createObjectURL(chosen);
    const seconds = await videoDuration(url);
    URL.revokeObjectURL(url);
    if (seconds) form.set("duration_seconds", seconds);
  };
  const readLink = async () => {
    if (type !== "url" || !form.values.video_url.startsWith("https://")) return;
    const seconds = await videoDuration(form.values.video_url);
    if (seconds) form.set("duration_seconds", seconds);
  };

  const submit = form.submit(async (values) => {
    const data = new FormData();
    Object.entries(values).forEach(([k, v]) => data.append(k, v));
    if (type === "upload" && file) data.append("video", file);
    try {
      setPercent(0);
      await api.upload(lesson ? `/manage/lessons/${lesson.id}` : `/manage/courses/${course.id}/lessons`,
        data, { method: lesson ? "PUT" : "POST", onProgress: setPercent });
      onDone();
    } finally {
      setPercent(null);
    }
  });

  return (
    <Modal title={lesson ? "Edit lesson" : "Add lesson"} onClose={() => !form.busy && onClose()} wide>
      <form onSubmit={submit} noValidate>
        <Alert type="error">{form.message}</Alert>
        <Field label="Lesson title" maxLength={150} {...form.bind("title")} />
        <Field label="Video source" as="select" {...form.bind("video_type")}>
          <option value="upload">Upload a video file</option>
          <option value="youtube">YouTube link</option>
          <option value="url">Direct video link (MP4 or WebM)</option>
          <option value="none">No video (reading lesson)</option>
        </Field>
        {type === "upload" && (
          <Field label={hasUpload ? "Replace video (optional)" : "Video file"} type="file" accept=".mp4,.webm"
            onChange={chooseFile} error={form.errors.video} hint="MP4 or WebM." />
        )}
        {(type === "youtube" || type === "url") && (
          <Field label="Video link" type="url" placeholder="https://..." {...form.bind("video_url")} onBlur={readLink} />
        )}
        {type !== "none" && (
          <Field label="Duration in seconds" type="number" min={0} max={86400} {...form.bind("duration_seconds")}
            hint={type === "youtube" ? "Optional. Shown to students." : "Filled in automatically when possible. Needed for automatic completion."} />
        )}
        <Field label="Lesson notes" as="textarea" rows={7} maxLength={20000} {...form.bind("content")} />
        {percent !== null && type === "upload" && file && (
          <div className="upload-status" role="status">
            <progress max={100} value={percent} /> {percent < 100 ? `Uploading ${percent}%` : "Saving the video..."}
          </div>
        )}
        <div className="actions end">
          <Button variant="outline" onClick={onClose} disabled={form.busy}>Cancel</Button>
          <Button type="submit" busy={form.busy}>Save lesson</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function LessonsPanel({ course, lessons, reload }) {
  const toast = useToast();
  const [editing, setEditing] = useState(undefined); // undefined: closed, null: new
  const run = async (action, success) => {
    try {
      await action();
      if (success) toast.success(success);
      await reload();
    } catch (error) {
      toast.error(error.message);
    }
  };
  const move = (index, step) => {
    const ids = lessons.map((l) => l.id);
    [ids[index], ids[index + step]] = [ids[index + step], ids[index]];
    run(() => api.put(`/manage/courses/${course.id}/lesson-order`, { lesson_ids: ids }));
  };
  const remove = async (lesson) => {
    const sure = await toast.confirm({
      title: "Delete lesson?", danger: true, action: "Delete",
      text: `"${lesson.title}" and the students' progress for it will be deleted.`,
    });
    if (sure) run(() => api.delete(`/manage/lessons/${lesson.id}`), "Lesson deleted.");
  };

  return (
    <section className="panel">
      <div className="section-head">
        <h2>Lessons</h2>
        <Button onClick={() => setEditing(null)}><FiPlus aria-hidden="true" /> Add lesson</Button>
      </div>
      {!lessons.length && <EmptyState title="No lessons yet" text="Add a lesson before publishing the course." />}
      <ol className="manage-list">
        {lessons.map((lesson, index) => (
          <li key={lesson.id}>
            <div className="grow">
              <strong>{index + 1}. {lesson.title}</strong>
              <small className="block">{SOURCES[lesson.video_type]} {formatDuration(lesson.duration_seconds)}</small>
            </div>
            <div className="row-actions">
              <Button variant="outline" size="sm" disabled={index === 0} onClick={() => move(index, -1)} aria-label="Move up"><FiArrowUp /></Button>
              <Button variant="outline" size="sm" disabled={index === lessons.length - 1} onClick={() => move(index, 1)} aria-label="Move down"><FiArrowDown /></Button>
              <Button variant="outline" size="sm" onClick={() => setEditing(lesson)}><FiEdit aria-hidden="true" /> Edit</Button>
              <Button variant="danger" size="sm" onClick={() => remove(lesson)} aria-label={`Delete ${lesson.title}`}><FiTrash2 /></Button>
            </div>
          </li>
        ))}
      </ol>
      {editing !== undefined && (
        <LessonForm course={course} lesson={editing} onClose={() => setEditing(undefined)}
          onDone={() => { setEditing(undefined); toast.success("Lesson saved."); reload(); }} />
      )}
    </section>
  );
}
