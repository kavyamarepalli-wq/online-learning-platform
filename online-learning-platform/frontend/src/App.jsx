import { useEffect } from "react";
import { Footer, Navbar } from "./components/Layout.jsx";
import { Alert, Button, EmptyState, Spinner } from "./components/ui.jsx";
import { homeFor, useAuth } from "./lib/auth.jsx";
import { Link, matchPath, navigate, useLocation } from "./lib/router.jsx";
import AdminDashboard from "./pages/admin/AdminDashboard.jsx";
import CourseDetails from "./pages/CourseDetails.jsx";
import Courses from "./pages/Courses.jsx";
import Home from "./pages/Home.jsx";
import Learn from "./pages/Learn.jsx";
import Login from "./pages/Login.jsx";
import CourseEditor from "./pages/manage/CourseEditor.jsx";
import InstructorDashboard from "./pages/manage/InstructorDashboard.jsx";
import Profile from "./pages/Profile.jsx";
import { Quiz, QuizResult } from "./pages/Quiz.jsx";
import Register from "./pages/Register.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import Verify from "./pages/Verify.jsx";

// roles: undefined = public, [] = any signed-in user, [..] = only those roles.
const ROUTES = [
  ["/", Home],
  ["/courses", Courses],
  ["/courses/:id", CourseDetails],
  ["/login", Login],
  ["/register", Register],
  ["/verify", Verify],
  ["/verify/:code", Verify],
  ["/dashboard", StudentDashboard, ["student"]],
  ["/learn/:id", Learn, []],
  ["/quizzes/:id", Quiz, []],
  ["/results/:id", QuizResult, []],
  ["/profile", Profile, []],
  ["/instructor", InstructorDashboard, ["instructor"]],
  ["/manage/courses/new", CourseEditor, ["instructor", "admin"]],
  ["/manage/courses/:id", CourseEditor, ["instructor", "admin"]],
  ["/admin", AdminDashboard, ["admin"]],
];

function RedirectToLogin() {
  useEffect(() => {
    const next = window.location.pathname + window.location.search;
    navigate(`/login?next=${encodeURIComponent(next)}`, { replace: true });
  }, []);
  return null;
}

function NotFound() {
  return (
    <div className="container section">
      <EmptyState title="Page not found" text="The page you are looking for does not exist.">
        <Link to="/" className="btn btn-primary">Go to the home page</Link>
      </EmptyState>
    </div>
  );
}

function Page() {
  const { path } = useLocation();
  const { user, ready, problem, retry } = useAuth();

  // Wait until a saved sign-in is restored, so pages load once with the right user.
  if (!ready && !problem) return <Spinner />;

  for (const [pattern, Component, roles] of ROUTES) {
    const params = matchPath(pattern, path);
    if (!params) continue;
    if (roles) {
      if (problem && !user) {
        return (
          <div className="container section">
            <Alert type="error">{problem}</Alert>
            <Button onClick={retry}>Try again</Button>
          </div>
        );
      }
      if (!user) return <RedirectToLogin />;
      if (roles.length && !roles.includes(user.role)) {
        return (
          <div className="container section">
            <EmptyState title="No access" text="Your account does not have access to this page.">
              <Link to={homeFor(user)} className="btn btn-primary">Go to my dashboard</Link>
            </EmptyState>
          </div>
        );
      }
    }
    // The key resets page state when moving between two records of the same type.
    return <Component key={`${pattern}:${JSON.stringify(params)}:${user?.id ?? 0}`} params={params} />;
  }
  return <NotFound />;
}

export default function App() {
  return (
    <>
      <a href="#main" className="skip-link">Skip to content</a>
      <Navbar />
      <main id="main"><Page /></main>
      <Footer />
    </>
  );
}
