import { FiAward, FiBookOpen, FiCheckSquare, FiTrendingUp, FiUserCheck, FiUsers } from "react-icons/fi";
import { Alert, Button, EmptyState, Loadable, Stat } from "../../components/ui.jsx";
import { plural } from "../../lib/format.js";
import { useApi } from "../../lib/hooks.js";
import { ActivityList } from "./Monitoring.jsx";

function EnrollmentChart({ days }) {
  const max = Math.max(...days.map((d) => d.total), 1);
  const total = days.reduce((sum, d) => sum + d.total, 0);
  const short = (date) => new Date(`${date}T00:00:00Z`).toLocaleDateString(undefined, { day: "numeric", month: "short", timeZone: "UTC" });
  return (
    <figure className="chart">
      <figcaption>{plural(total, "new enrollment")} in the last 14 days (UTC)</figcaption>
      <div className="bars">
        {days.map((d, i) => (
          <div key={d.date} className="bar" title={`${short(d.date)}: ${d.total}`}>
            <span className="bar-value">{d.total || ""}</span>
            <span className="bar-fill" style={{ height: `${(d.total / max) * 100}%` }} />
            <span className={`bar-label ${i % 3 === 1 ? "" : "optional"}`}>{short(d.date)}</span>
            <span className="sr-only">{short(d.date)}: {d.total}</span>
          </div>
        ))}
      </div>
    </figure>
  );
}

export default function Overview({ open }) {
  const state = useApi("/admin/overview");
  return (
    <Loadable state={state}>
      {({ counts, enrollments_by_day: days, top_courses: top, recent_activity: recent }) => (
        <>
          {counts.pending_instructors > 0 && (
            <div className="notice">
              <Alert>{plural(counts.pending_instructors, "instructor")} waiting for approval.</Alert>
              <Button size="sm" onClick={() => open("instructors")}>Review</Button>
            </div>
          )}
          <div className="stats-row">
            <Stat icon={FiUsers} value={counts.students} label="Students" />
            <Stat icon={FiUserCheck} value={counts.instructors} label="Instructors" />
            <Stat icon={FiBookOpen} value={`${counts.published_courses}/${counts.courses}`} label="Published courses" />
            <Stat icon={FiTrendingUp} value={counts.enrollments} label="Enrollments" />
            <Stat icon={FiCheckSquare} value={counts.quiz_attempts ? `${Math.round((counts.quiz_passes / counts.quiz_attempts) * 100)}%` : "–"}
              label={`Quiz pass rate (${plural(counts.quiz_attempts, "attempt")})`} />
            <Stat icon={FiAward} value={counts.certificates} label="Certificates" />
          </div>
          <div className="split even">
            <section className="panel">
              <h2>Enrollment trend</h2>
              <EnrollmentChart days={days} />
            </section>
            <section className="panel">
              <h2>Top courses</h2>
              {!top.length && <EmptyState title="No courses yet" />}
              <ul className="manage-list">
                {top.map((c) => (
                  <li key={c.id}>
                    <strong className="grow">{c.title}</strong>
                    <small>{plural(c.students, "student")} · {c.completions} completed</small>
                  </li>
                ))}
              </ul>
            </section>
          </div>
          <section className="panel">
            <h2>Recent activity</h2>
            <ActivityList items={recent} />
          </section>
        </>
      )}
    </Loadable>
  );
}
