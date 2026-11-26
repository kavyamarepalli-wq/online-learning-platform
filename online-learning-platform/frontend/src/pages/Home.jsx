import { useState } from "react";
import { FiArrowRight, FiAward, FiBarChart2, FiBookOpen, FiCheckSquare, FiPlayCircle, FiSearch, FiUserCheck, FiUsers } from "react-icons/fi";
import CourseCard from "../components/CourseCard.jsx";
import { EmptyState, Loadable, Stat } from "../components/ui.jsx";
import { homeFor, useAuth } from "../lib/auth.jsx";
import { plural } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { Link, navigate } from "../lib/router.jsx";

const FEATURES = [
  [FiPlayCircle, "Video lessons", "Watch at your pace and resume where you stopped."],
  [FiCheckSquare, "Instant quizzes", "Check what you learned with automatically scored quizzes."],
  [FiBarChart2, "Progress tracking", "See your completion percentage for every course."],
  [FiAward, "Certificates", "Finish a course and download a verifiable certificate."],
];

export default function Home() {
  useTitle("");
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const featured = useApi("/courses?featured=1&sort=popular&per_page=6");
  const stats = useApi("/stats");

  const search = (event) => {
    event.preventDefault();
    navigate(`/courses${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ""}`);
  };

  return (
    <>
      <section className="hero">
        <div className="container hero-inner">
          <div>
            <span className="eyebrow">Online learning platform</span>
            <h1>Build new skills, one lesson at a time</h1>
            <p>Enroll in courses, watch video lessons, download study materials, take quizzes and earn certificates.</p>
            <form className="hero-search" onSubmit={search} role="search">
              <FiSearch aria-hidden="true" />
              <input type="search" value={query} onChange={(e) => setQuery(e.target.value)}
                placeholder="What do you want to learn?" aria-label="Search courses" />
              <button type="submit" className="btn btn-accent">Search</button>
            </form>
            <div className="actions">
              <Link to="/courses" className="btn btn-light">Explore courses <FiArrowRight aria-hidden="true" /></Link>
              <Link to={user ? homeFor(user) : "/register"} className="btn btn-ghost">
                {user ? "Go to my dashboard" : "Join for free"}
              </Link>
            </div>
          </div>
          <div className="hero-panel" aria-hidden="true">
            {FEATURES.map(([Icon, title], index) => (
              <div key={title} className="hero-tile" style={{ marginLeft: `${(index % 2) * 28}px` }}>
                <Icon /> <span>{title}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {stats.data && (
        <section className="container stats-band" aria-label="Platform statistics">
          <Stat icon={FiBookOpen} value={stats.data.courses} label="Courses" />
          <Stat icon={FiUsers} value={stats.data.students} label="Students" />
          <Stat icon={FiUserCheck} value={stats.data.instructors} label="Instructors" />
          <Stat icon={FiAward} value={stats.data.certificates} label="Certificates issued" />
        </section>
      )}

      <section className="container section">
        <div className="section-head">
          <div>
            <h2>Featured courses</h2>
            <p>Hand-picked courses to start with.</p>
          </div>
          <Link to="/courses" className="btn btn-outline">View all</Link>
        </div>
        <Loadable state={featured}>
          {(data) => data.items.length
            ? <div className="grid">{data.items.map((c) => <CourseCard key={c.id} course={c} />)}</div>
            : <EmptyState title="No featured courses yet" text="Browse the catalogue to see what is available." />}
        </Loadable>
      </section>

      {stats.data?.categories.length > 0 && (
        <section className="container section">
          <h2>Browse by category</h2>
          <div className="category-list">
            {stats.data.categories.map((c) => (
              <Link key={c.category} to={`/courses?category=${encodeURIComponent(c.category)}`} className="category">
                <strong>{c.category}</strong>
                <span>{plural(c.total, "course")}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="section band">
        <div className="container">
          <h2>Everything you need to learn online</h2>
          <div className="grid four">
            {FEATURES.map(([Icon, title, text]) => (
              <div key={title} className="card feature">
                <span className="stat-icon"><Icon aria-hidden="true" /></span>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
