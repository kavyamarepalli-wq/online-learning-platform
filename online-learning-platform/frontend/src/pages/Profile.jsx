import { Alert, Badge, Button, Field, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { useAuth } from "../lib/auth.jsx";
import { checks, formatDate } from "../lib/format.js";
import { useForm, useTitle } from "../lib/hooks.js";
import { PasswordField } from "./Login.jsx";

export default function Profile() {
  useTitle("My profile");
  const { user, updateUser, signIn } = useAuth();
  const toast = useToast();
  const teaching = user.role === "instructor";

  const profile = useForm(
    { name: user.name, headline: user.headline || "", bio: user.bio || "", expertise: user.expertise || "" },
    (v) => ({
      name: checks.min(v.name, 2, "Name"),
      headline: teaching ? checks.min(v.headline, 3, "Professional headline") : "",
    }));
  const password = useForm({ current_password: "", new_password: "", confirm: "" }, (v) => ({
    current_password: v.current_password ? "" : "Enter your current password.",
    new_password: checks.password(v.new_password),
    confirm: v.confirm === v.new_password ? "" : "Passwords do not match.",
  }));

  const saveProfile = profile.submit(async (values) => {
    updateUser((await api.put("/auth/profile", values)).user);
    toast.success("Profile saved.");
  });
  const savePassword = password.submit(async ({ confirm, ...values }) => {
    signIn(await api.put("/auth/password", values));
    password.setValues({ current_password: "", new_password: "", confirm: "" });
    toast.success("Password changed. Other devices have been signed out.");
  });

  return (
    <div className="container section narrow">
      <h1>My profile</h1>
      <p className="meta">{user.email} <Badge tone="primary">{user.role}</Badge> Member since {formatDate(user.created_at)}</p>
      <form className="panel" onSubmit={saveProfile} noValidate>
        <h2>Details</h2>
        <Alert type="error">{profile.message}</Alert>
        <Field label="Full name" maxLength={100} {...profile.bind("name")} />
        {teaching && (
          <>
            <Field label="Professional headline" maxLength={150} {...profile.bind("headline")} />
            <Field label="Bio" as="textarea" rows={4} maxLength={2000} {...profile.bind("bio")} />
            <Field label="Expertise" maxLength={200} {...profile.bind("expertise")} />
          </>
        )}
        <Button type="submit" busy={profile.busy}>Save details</Button>
      </form>
      <form className="panel" onSubmit={savePassword} noValidate>
        <h2>Change password</h2>
        <Alert type="error">{password.message}</Alert>
        <PasswordField label="Current password" autoComplete="current-password" {...password.bind("current_password")} />
        <PasswordField label="New password" autoComplete="new-password" {...password.bind("new_password")} />
        <PasswordField label="Confirm new password" autoComplete="new-password" {...password.bind("confirm")} />
        <Button type="submit" busy={password.busy}>Change password</Button>
      </form>
    </div>
  );
}
