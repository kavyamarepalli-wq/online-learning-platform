import { useRef, useState } from "react";
import { FiDownload, FiTrash2, FiUpload } from "react-icons/fi";
import { Alert, Button, EmptyState, Field, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { checks, formatSize } from "../../lib/format.js";
import { useForm } from "../../lib/hooks.js";

export default function MaterialsPanel({ course, materials, lessons, reload }) {
  const toast = useToast();
  const input = useRef(null);
  const [file, setFile] = useState(null);
  const form = useForm({ title: "", lesson_id: "" }, (v) => ({
    title: checks.min(v.title, 2, "Title"),
    file: !file ? "Choose a file." : file.size > 25 * 1024 * 1024 ? "The file must be 25 MB or smaller." : "",
  }));

  const submit = form.submit(async (values) => {
    const data = new FormData();
    data.append("title", values.title);
    data.append("lesson_id", values.lesson_id);
    data.append("file", file);
    await api.upload(`/manage/courses/${course.id}/materials`, data);
    form.setValues({ title: "", lesson_id: "" });
    setFile(null);
    input.current.value = "";
    toast.success("Material uploaded.");
    reload();
  });

  const remove = async (material) => {
    const sure = await toast.confirm({
      title: "Delete material?", danger: true, action: "Delete", text: `"${material.title}" will be removed.`,
    });
    if (!sure) return;
    try {
      await api.delete(`/manage/materials/${material.id}`);
      toast.success("Material deleted.");
      reload();
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <div className="split">
      <section className="panel">
        <h2>Study materials</h2>
        {!materials.length && <EmptyState title="No materials yet" />}
        <ul className="manage-list">
          {materials.map((m) => (
            <li key={m.id}>
              <div className="grow">
                <strong>{m.title}</strong>
                <small className="block">{m.file_name} · {formatSize(m.file_size)}
                  {m.lesson_id ? ` · ${lessons.find((l) => l.id === m.lesson_id)?.title ?? ""}` : ""}</small>
              </div>
              <div className="row-actions">
                <a className="btn btn-outline btn-sm" href={m.download_url} download={m.file_name} aria-label={`Download ${m.title}`}><FiDownload /></a>
                <Button variant="danger" size="sm" onClick={() => remove(m)} aria-label={`Delete ${m.title}`}><FiTrash2 /></Button>
              </div>
            </li>
          ))}
        </ul>
      </section>
      <form className="panel" onSubmit={submit} noValidate>
        <h2>Upload material</h2>
        <Alert type="error">{form.message}</Alert>
        <Field label="Title" maxLength={150} {...form.bind("title")} />
        <Field label="Related lesson (optional)" as="select" {...form.bind("lesson_id")}>
          <option value="">Whole course</option>
          {lessons.map((l) => <option key={l.id} value={l.id}>{l.title}</option>)}
        </Field>
        <div className={`field ${form.errors.file ? "has-error" : ""}`}>
          <label htmlFor="material-file">File</label>
          <input id="material-file" ref={input} type="file" accept=".pdf,.zip,.txt,.md,.csv,.png,.jpg,.jpeg,.docx,.pptx,.xlsx"
            onChange={(e) => setFile(e.target.files[0] || null)} />
          <small className={form.errors.file ? "error-text" : "hint"}>
            {form.errors.file || "PDF, Office files, ZIP, text or images, up to 25 MB."}
          </small>
        </div>
        <Button type="submit" busy={form.busy}><FiUpload aria-hidden="true" /> Upload</Button>
      </form>
    </div>
  );
}
