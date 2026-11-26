import { useState } from "react";
import { FiAward, FiBookOpen, FiCheckCircle, FiDownload, FiTrendingUp, FiExternalLink } from "react-icons/fi";
import { Thumbnail } from "../components/CourseCard.jsx";
import { Badge, Button, EmptyState, Loadable, ProgressBar, Stat, Table, Tabs, useToast } from "../components/ui.jsx";
import { api } from "../lib/api.js";
import { useAuth } from "../lib/auth.jsx";
import { formatDate, formatDateTime, plural } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { Link, navigate, useQuery } from "../lib/router.jsx";

function MyCourses({ enrollments }) {
  if (!enrollments.length) {
    return (
      <EmptyState title="You have not enrolled in a course yet" text="Find something you would like to learn.">
        <Link to="/courses" className="btn btn-primary">Browse courses</Link>
      </EmptyState>
    );
  }
  return (
    <div className="grid">
      {enrollments.map((e) => (
        <article key={e.enrollment_id} className="card">
          <Thumbnail src={e.thumbnail_url} title={e.course_title} />
          <div className="card-body">
            <div className="badges">
              <Badge tone="primary">{e.category}</Badge>
              {e.is_completed && <Badge tone="success">Completed</Badge>}
            </div>
            <h3>{e.course_title}</h3>
            <p className="meta">{e.instructor_name}</p>
            <ProgressBar value={e.percentage} label={`Progress in ${e.course_title}`} />
            <p className="meta">
              {e.completed_lessons}/{e.total_lessons} lessons · {e.passed_quizzes}/{e.total_quizzes} quizzes
            </p>
            <Link to={`/learn/${e.course_id}`} className="btn btn-primary btn-block push">
              {e.percentage === 0 ? "Start learning" : e.percentage >= 100 ? "Review course" : "Continue learning"}
            </Link>
          </div>
        </article>
      ))}
    </div>
  );
}

function Certificates({ certificates }) {
  const toast = useToast();
  const [busy, setBusy] = useState(null);
  const download = async (c) => {
    setBusy(c.id);
    try {
      await api.download(`/certificates/${c.id}/download`, `certificate-${c.code}.pdf`);
    } catch (error) {
      toast.error(error.message);
    }
    setBusy(null);
  };
  if (!certificates.length) {
    return <EmptyState title="No certificates yet" text="Complete every lesson and pass every quiz in a course to earn one." />;
  }
  return (
    <div className="grid">
      {certificates.map((c) => (
        <article key={c.id} className="card certificate-card">
          <div className="card-body">
            <FiAward className="big-icon" aria-hidden="true" />
            <h3>{c.course_title}</h3>
            <p className="meta">Issued {formatDate(c.issued_at)} · {c.instructor_name}</p>
            <p className="code">{c.code}</p>
            <div className="actions push">
              <Button busy={busy === c.id} onClick={() => download(c)}><FiDownload aria-hidden="true" /> Download PDF</Button>
              <Link to={`/verify/${c.code}`} className="btn btn-outline"><FiExternalLink aria-hidden="true" /> Verify</Link>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export default function StudentDashboard() {
  useTitle("My learning");
  const { user } = useAuth();
  const state = useApi("/student/dashboard");
  const tab = useQuery().get("tab") || "courses";

  return (
    <div className="container section">
      <h1>Hello, {user.name}</h1>
      <p>Here is how your learning is going.</p>
      <Loadable state={state}>
        {({ stats, enrollments, results, certificates, achievements }) => (
          <>
            <div className="stats-row">
              <Stat icon={FiBookOpen} value={stats.enrolled} label="Enrolled courses" />
              <Stat icon={FiCheckCircle} value={stats.completed} label="Completed courses" />
              <Stat icon={FiTrendingUp} value={stats.average_score === null ? "–" : `${stats.average_score}%`} label="Average quiz score" />
              <Stat icon={FiAward} value={stats.certificates} label="Certificates" />
            </div>
            <Tabs active={tab} onChange={(t) => navigate(`/dashboard?tab=${t}`, { replace: true, scroll: false })}
              tabs={[["courses", "My courses"], ["scores", "Quiz scores"], ["achievements", "Achievements"], ["certificates", "Certificates"]]} />
            {tab === "courses" && <MyCourses enrollments={enrollments} />}
            {tab === "scores" && (
              <Table rows={results} empty="You have not taken a quiz yet." columns={[
                ["Quiz", (r) => <Link to={`/results/${r.id}`}>{r.quiz_title}</Link>],
                ["Course", (r) => r.course_title],
                ["Score", (r) => `${r.percentage}% (${r.score}/${r.total})`],
                ["Result", (r) => <Badge tone={r.passed ? "success" : "danger"}>{r.passed ? "Passed" : "Failed"}</Badge>],
                ["Date", (r) => formatDateTime(r.submitted_at)],
              ]} />
            )}
            {tab === "achievements" && (
              <>
                <p>{plural(achievements.filter((a) => a.earned).length, "achievement")} earned of {achievements.length}.</p>
                <div className="grid">
                  {achievements.map((a) => (
                    <div key={a.code} className={`card achievement ${a.earned ? "earned" : ""}`}>
                      <div className="card-body">
                        <FiAward className="big-icon" aria-hidden="true" />
                        <h3>{a.title}</h3>
                        <p>{a.description}</p>
                        {a.earned ? <Badge tone="success">Earned</Badge>
                          : <ProgressBar value={Math.floor((a.progress / a.target) * 100)} label={a.title} />}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
            {tab === "certificates" && <Certificates certificates={certificates} />}
          </>
        )}
      </Loadable>
    </div>
  );
}
