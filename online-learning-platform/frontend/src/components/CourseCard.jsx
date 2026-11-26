import { FiBookOpen, FiUser, FiUsers } from "react-icons/fi";
import { formatDuration, plural } from "../lib/format.js";
import { Link } from "../lib/router.jsx";
import { Badge } from "./ui.jsx";

export function Thumbnail({ src, title, className = "thumb" }) {
  return src
    ? <img className={className} src={src} alt="" loading="lazy" width="800" height="450" />
    : <div className={`${className} thumb-empty`} aria-hidden="true">{title.slice(0, 1).toUpperCase()}</div>;
}

export default function CourseCard({ course }) {
  return (
    <article className="card course-card">
      <Thumbnail src={course.thumbnail_url} title={course.title} />
      <div className="card-body">
        <div className="badges">
          <Badge tone="primary">{course.category}</Badge>
          <Badge>{course.level}</Badge>
        </div>
        <h3>
          {/* The link stretches over the whole card. */}
          <Link to={`/courses/${course.id}`} className="stretched">{course.title}</Link>
        </h3>
        <p className="clamp">{course.summary}</p>
        <p className="meta"><FiUser aria-hidden="true" /> {course.instructor.name}</p>
        <div className="card-foot">
          <span className="meta">
            <FiBookOpen aria-hidden="true" /> {plural(course.lesson_count, "lesson")}
            {course.duration_seconds ? ` · ${formatDuration(course.duration_seconds)}` : ""}
          </span>
          <span className="meta"><FiUsers aria-hidden="true" /> {plural(course.student_count, "student")}</span>
        </div>
      </div>
    </article>
  );
}
