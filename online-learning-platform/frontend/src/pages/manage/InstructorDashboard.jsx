import { useEffect } from "react";
import { FiBookOpen, FiCheckCircle, FiUsers } from "react-icons/fi";
import { Alert, Button, Stat } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { useAuth } from "../../lib/auth.jsx";
import { useApi, useTitle } from "../../lib/hooks.js";
import CourseTable from "./CourseTable.jsx";

export function PendingApproval() {
  const { updateUser } = useAuth();
  const check = () => api.get("/auth/me").then((r) => updateUser(r.user)).catch(() => {});
  return (
    <div className="panel">
      <Alert>Your instructor account is waiting for approval by an administrator. You can create courses once it is approved.</Alert>
      <Button variant="outline" onClick={check}>Check again</Button>
    </div>
  );
}

function Summary() {
  const { data } = useApi("/manage/courses");
  if (!data) return null;
  return (
    <div className="stats-row">
      <Stat icon={FiBookOpen} value={data.items.length} label="Courses" />
      <Stat icon={FiCheckCircle} value={data.items.filter((c) => c.status === "published").length} label="Published" />
      <Stat icon={FiUsers} value={data.items.reduce((sum, c) => sum + c.student_count, 0)} label="Enrollments" />
    </div>
  );
}

export default function InstructorDashboard() {
  useTitle("Instructor studio");
  const { user, updateUser } = useAuth();
  // Approval may have changed since the last sign-in.
  useEffect(() => { api.get("/auth/me").then((r) => updateUser(r.user)).catch(() => {}); }, []);

  return (
    <div className="container section">
      <h1>Instructor studio</h1>
      <p>Create courses, upload content and follow your students.</p>
      {user.is_approved ? <><Summary /><CourseTable /></> : <PendingApproval />}
    </div>
  );
}
