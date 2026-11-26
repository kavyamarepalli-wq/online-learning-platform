import { Tabs } from "../../components/ui.jsx";
import { useTitle } from "../../lib/hooks.js";
import { navigate, useQuery } from "../../lib/router.jsx";
import CourseTable from "../manage/CourseTable.jsx";
import { Activity, Enrollments, Results } from "./Monitoring.jsx";
import Overview from "./Overview.jsx";
import Users from "./Users.jsx";

const TABS = [
  ["overview", "Overview"], ["students", "Students"], ["instructors", "Instructors"], ["admins", "Admins"],
  ["courses", "Courses"], ["enrollments", "Enrollments"], ["results", "Quiz results"], ["activity", "Activity"],
];

export default function AdminDashboard() {
  useTitle("Admin dashboard");
  const tab = useQuery().get("tab") || "overview";
  const open = (key) => navigate(`/admin?tab=${key}`, { replace: true, scroll: false });
  return (
    <div className="container section">
      <h1>Admin dashboard</h1>
      <Tabs tabs={TABS} active={tab} onChange={open} />
      {tab === "overview" && <Overview open={open} />}
      {tab === "students" && <Users key="student" role="student" />}
      {tab === "instructors" && <Users key="instructor" role="instructor" />}
      {tab === "admins" && <Users key="admin" role="admin" />}
      {tab === "courses" && <CourseTable showInstructor />}
      {tab === "enrollments" && <Enrollments />}
      {tab === "results" && <Results />}
      {tab === "activity" && <Activity />}
    </div>
  );
}
