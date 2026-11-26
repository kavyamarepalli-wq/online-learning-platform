import { useEffect } from "react";
import { Alert, Button, Field, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { useAuth } from "../lib/auth.jsx";
import { checks } from "../lib/format.js";
import { useForm, useTitle } from "../lib/hooks.js";
import { Link, navigate, useQuery } from "../lib/router.jsx";
import { PasswordField, safeNext } from "./Login.jsx";

export default function Register() {
  useTitle("Sign up");
  const { user, signIn } = useAuth();
  const toast = useToast();
  const query = useQuery();
  const next = query.get("next");
  const form = useForm(
    {
      name: "", email: "", password: "", confirm: "", headline: "", bio: "",
      role: query.get("role") === "instructor" ? "instructor" : "student",
    },
    (v) => ({
      name: checks.min(v.name, 2, "Name"),
      email: checks.email(v.email),
      password: checks.password(v.password),
      confirm: v.confirm === v.password ? "" : "Passwords do not match.",
      headline: v.role === "instructor" ? checks.min(v.headline, 3, "Professional headline") : "",
    }));
  const teaching = form.values.role === "instructor";

  useEffect(() => {
    if (user) navigate(safeNext(next, user), { replace: true });
  }, [user]);

  const submit = form.submit(async ({ confirm, ...values }) => {
    const session = await api.post("/auth/register", values);
    toast.success(session.user.role === "instructor"
      ? "Account created. An administrator must approve it before you can add courses."
      : "Account created. Welcome to LearnSphere!");
    signIn(session);
  });

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <h1>Create your account</h1>
        <p>It only takes a minute.</p>
        <Alert type="error">{form.message}</Alert>
        <fieldset className="role-picker">
          <legend>I want to</legend>
          {[["student", "Learn", "Student"], ["instructor", "Teach", "Instructor"]].map(([value, verb, label]) => (
            <label key={value} className={form.values.role === value ? "selected" : ""}>
              <input type="radio" name="role" value={value} checked={form.values.role === value}
                onChange={() => form.set("role", value)} />
              <strong>{verb}</strong>
              <span>{label}</span>
            </label>
          ))}
        </fieldset>
        <Field label="Full name" autoComplete="name" maxLength={100}
          hint="This name appears on your certificates." {...form.bind("name")} />
        <Field label="Email" type="email" autoComplete="email" {...form.bind("email")} />
        <PasswordField label="Password" autoComplete="new-password"
          hint="At least 8 characters with a letter and a number." {...form.bind("password")} />
        <PasswordField label="Confirm password" autoComplete="new-password" {...form.bind("confirm")} />
        {teaching && (
          <>
            <Field label="Professional headline" maxLength={150} placeholder="e.g. Web developer"
              {...form.bind("headline")} />
            <Field label="Short bio (optional)" as="textarea" rows={3} maxLength={2000} {...form.bind("bio")} />
          </>
        )}
        <Button type="submit" className="btn-block" busy={form.busy}>Sign up</Button>
        <p className="center">
          Already registered? <Link to={`/login${next ? `?next=${encodeURIComponent(next)}` : ""}`}>Log in</Link>
        </p>
      </form>
    </div>
  );
}
