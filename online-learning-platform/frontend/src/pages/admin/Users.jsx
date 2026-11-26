import { useState } from "react";
import { FiEdit, FiPlus, FiTrash2 } from "react-icons/fi";
import { Alert, Badge, Button, Field, Loadable, Modal, Pagination, Table, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { useAuth } from "../../lib/auth.jsx";
import { checks, formatDate } from "../../lib/format.js";
import { useForm } from "../../lib/hooks.js";
import { PasswordField } from "../Login.jsx";
import { useList } from "./Monitoring.jsx";

function UserForm({ role, user, onClose, onDone }) {
  const { user: me, updateUser } = useAuth();
  const self = user?.id === me.id;
  const form = useForm(
    { name: user?.name || "", email: user?.email || "", password: "", headline: "", is_active: user?.is_active ?? true },
    (v) => ({
      name: checks.min(v.name, 2, "Name"),
      email: checks.email(v.email),
      password: user && !v.password ? "" : checks.password(v.password),
    }));
  const submit = form.submit(async (v) => {
    if (user) {
      const reply = await api.put(`/admin/users/${user.id}`,
        { name: v.name, email: v.email, is_active: v.is_active, ...(v.password && { password: v.password }) });
      if (self) updateUser(reply.user);
    } else {
      await api.post("/admin/users", { name: v.name, email: v.email, password: v.password, headline: v.headline, role });
    }
    onDone(user ? "User saved." : "User added.");
  });
  return (
    <Modal title={user ? `Edit ${role}` : `Add ${role}`} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <Alert type="error">{form.message}</Alert>
        <Field label="Full name" maxLength={100} {...form.bind("name")} />
        <Field label="Email" type="email" autoComplete="off" {...form.bind("email")} />
        {!self && (
          <PasswordField label={user ? "New password (optional)" : "Password"} autoComplete="new-password" {...form.bind("password")} />
        )}
        {!user && role === "instructor" && <Field label="Headline (optional)" maxLength={150} {...form.bind("headline")} />}
        {user && !self && (
          <label className="checkbox">
            <input type="checkbox" checked={form.values.is_active} onChange={(e) => form.set("is_active", e.target.checked)} />
            Account is active (can log in)
          </label>
        )}
        <div className="actions end">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button type="submit" busy={form.busy}>Save</Button>
        </div>
      </form>
    </Modal>
  );
}

export default function Users({ role }) {
  const { state, search, setPage } = useList("/admin/users", `&role=${role}`);
  const { user: me } = useAuth();
  const toast = useToast();
  const [editing, setEditing] = useState(undefined);

  const run = async (action, success) => {
    try {
      await action();
      toast.success(success);
      state.reload();
    } catch (error) {
      toast.error(error.message);
    }
  };
  const remove = async (user) => {
    const sure = await toast.confirm({
      title: "Delete user?", danger: true, action: "Delete",
      text: `${user.name} (${user.email}) and their enrollments, results and certificates will be permanently deleted.`,
    });
    if (sure) run(() => api.delete(`/admin/users/${user.id}`), "User deleted.");
  };
  const approve = (user) => run(
    () => api.put(`/admin/instructors/${user.id}/approval`, { approved: !user.is_approved }),
    user.is_approved ? "Instructor approval removed." : "Instructor approved.");

  const columns = [
    ["Name", (u) => <><strong>{u.name}</strong><small className="block">{u.email}</small></>],
    ["Status", (u) => (
      <div className="badges">
        <Badge tone={u.is_active ? "success" : "danger"}>{u.is_active ? "Active" : "Deactivated"}</Badge>
        {role === "instructor" && <Badge tone={u.is_approved ? "primary" : "warning"}>{u.is_approved ? "Approved" : "Pending"}</Badge>}
      </div>
    )],
    ...(role === "student" ? [["Enrollments", (u) => u.enrollment_count]] : []),
    ...(role === "instructor" ? [["Courses", (u) => u.course_count]] : []),
    ["Joined", (u) => formatDate(u.created_at)],
    ["Last login", (u) => formatDate(u.last_login_at)],
    ["Actions", (u) => (
      <div className="row-actions">
        {role === "instructor" && (
          <Button variant={u.is_approved ? "outline" : "success"} size="sm" onClick={() => approve(u)}>
            {u.is_approved ? "Revoke approval" : "Approve"}
          </Button>
        )}
        <Button variant="outline" size="sm" onClick={() => setEditing(u)}><FiEdit aria-hidden="true" /> Edit</Button>
        {u.id !== me.id && (
          <Button variant="danger" size="sm" onClick={() => remove(u)} aria-label={`Delete ${u.name}`}><FiTrash2 /></Button>
        )}
      </div>
    )],
  ];

  return (
    <>
      <div className="section-head">
        {search(`Search ${role}s by name or email`)}
        <Button onClick={() => setEditing(null)}><FiPlus aria-hidden="true" /> Add {role}</Button>
      </div>
      <Loadable state={state}>
        {(data) => (
          <>
            <Table rows={data.items} columns={columns} empty={`No ${role}s found.`} />
            <Pagination page={data.page} pages={data.pages} onChange={setPage} />
          </>
        )}
      </Loadable>
      {editing !== undefined && (
        <UserForm role={role} user={editing} onClose={() => setEditing(undefined)}
          onDone={(message) => { setEditing(undefined); toast.success(message); state.reload(); }} />
      )}
    </>
  );
}
