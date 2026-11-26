import { useEffect, useState } from "react";
import { FiEye, FiEyeOff } from "react-icons/fi";
import { Alert, Button, Field, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { homeFor, useAuth } from "../lib/auth.jsx";
import { checks } from "../lib/format.js";
import { useForm, useTitle } from "../lib/hooks.js";
import { Link, navigate, useQuery } from "../lib/router.jsx";

// Only follow "next" addresses that stay on this site.
export function safeNext(next, user) {
  return next && /^\/(?![/\\])/.test(next) ? next : homeFor(user);
}

export function PasswordField(props) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="password-field">
      <Field {...props} type={visible ? "text" : "password"} />
      <button type="button" className="icon-btn" onClick={() => setVisible(!visible)}
        aria-label={visible ? "Hide password" : "Show password"}>
        {visible ? <FiEyeOff /> : <FiEye />}
      </button>
    </div>
  );
}

export default function Login() {
  useTitle("Log in");
  const { user, signIn } = useAuth();
  const toast = useToast();
  const next = useQuery().get("next");
  const form = useForm({ email: "", password: "" }, (v) => ({
    email: checks.email(v.email),
    password: v.password ? "" : "Password is required.",
  }));

  useEffect(() => {
    if (user) navigate(safeNext(next, user), { replace: true });
  }, [user]);

  const submit = form.submit(async (values) => {
    const session = await api.post("/auth/login", values);
    toast.success(`Welcome back, ${session.user.name}.`);
    signIn(session);
  });

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <h1>Welcome back</h1>
        <p>Log in to continue learning.</p>
        <Alert type="error">{form.message}</Alert>
        <Field label="Email" type="email" autoComplete="email" {...form.bind("email")} />
        <PasswordField label="Password" autoComplete="current-password" {...form.bind("password")} />
        <Button type="submit" className="btn-block" busy={form.busy}>Log in</Button>
        <p className="center">
          New here? <Link to={`/register${next ? `?next=${encodeURIComponent(next)}` : ""}`}>Create an account</Link>
        </p>
      </form>
    </div>
  );
}
