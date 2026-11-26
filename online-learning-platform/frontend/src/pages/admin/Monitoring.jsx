import { useEffect, useState } from "react";
import { Badge, Button, EmptyState, Field, Loadable, Pagination, ProgressBar, Table, useToast } from "../../components/ui.jsx";
import { api } from "../../lib/api.js";
import { formatDate, formatDateTime } from "../../lib/format.js";
import { useApi } from "../../lib/hooks.js";
import { Link } from "../../lib/router.jsx";

// A searchable, paginated list loaded from the API.
export function useList(endpoint, extra = "") {
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => {
    if (text.trim() === query) return undefined;
    const timer = setTimeout(() => { setQuery(text.trim()); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [text]);
  const state = useApi(`${endpoint}?page=${page}&q=${encodeURIComponent(query)}${extra}`);
  // Step back if the last item of the last page was removed.
  useEffect(() => {
    if (state.data && !state.loading && state.data.page > state.data.pages) setPage(state.data.pages);
  }, [state.data, state.loading]);
  const search = (label) => (
    <div className="list-search">
      <Field label={label} type="search" value={text} onChange={(e) => setText(e.target.value)} />
    </div>
  );
  return { state, search, setPage };
}

export function Enrollments() {
  const { state, search, setPage } = useList("/admin/enrollments");
  const toast = useToast();
  const remove = async (row) => {
    const sure = await toast.confirm({
      title: "Remove enrollment?", danger: true, action: "Remove",
      text: `${row.student_name} will be removed from "${row.course_title}" and lose lesson progress.`,
    });
    if (!sure) return;
    try {
      await api.delete(`/admin/enrollments/${row.enrollment_id}`);
      toast.success("Enrollment removed.");
      state.reload();
    } catch (error) {
      toast.error(error.message);
    }
  };
  return (
    <>
      {search("Search by student or course")}
      <Loadable state={state}>
        {(data) => (
          <>
            <Table rows={data.items} rowKey="enrollment_id" empty="No enrollments found." columns={[
              ["Student", (e) => <><strong>{e.student_name}</strong><small className="block">{e.student_email}</small></>],
              ["Course", (e) => e.course_title],
              ["Progress", (e) => <ProgressBar value={e.percentage} label={e.student_name} />],
              ["Enrolled", (e) => formatDate(e.enrolled_at)],
              ["Status", (e) => <Badge tone={e.is_completed ? "success" : "neutral"}>{e.is_completed ? "Completed" : "In progress"}</Badge>],
              ["Actions", (e) => <Button variant="danger" size="sm" onClick={() => remove(e)}>Remove</Button>],
            ]} />
            <Pagination page={data.page} pages={data.pages} onChange={setPage} />
          </>
        )}
      </Loadable>
    </>
  );
}

export function Results() {
  const { state, search, setPage } = useList("/admin/results");
  return (
    <>
      {search("Search by student, quiz or course")}
      <Loadable state={state}>
        {(data) => (
          <>
            <Table rows={data.items} empty="No quiz results found." columns={[
              ["Student", (r) => <><strong>{r.student_name}</strong><small className="block">{r.student_email}</small></>],
              ["Quiz", (r) => <><Link to={`/results/${r.id}`}>{r.quiz_title}</Link><small className="block">{r.course_title}</small></>],
              ["Score", (r) => `${r.percentage}% (${r.score}/${r.total})`],
              ["Result", (r) => <Badge tone={r.passed ? "success" : "danger"}>{r.passed ? "Passed" : "Failed"}</Badge>],
              ["Date", (r) => formatDateTime(r.submitted_at)],
            ]} />
            <Pagination page={data.page} pages={data.pages} onChange={setPage} />
          </>
        )}
      </Loadable>
    </>
  );
}

export function ActivityList({ items }) {
  if (!items.length) return <EmptyState title="No activity yet" />;
  return (
    <ul className="activity">
      {items.map((a) => (
        <li key={a.id}>
          <Badge tone="primary">{a.action.replaceAll("_", " ")}</Badge>
          <span className="grow"><strong>{a.user_name || "Deleted user"}</strong> {a.details}</span>
          <time dateTime={a.created_at}>{formatDateTime(a.created_at)}</time>
        </li>
      ))}
    </ul>
  );
}

export function Activity() {
  const { state, search, setPage } = useList("/admin/activity");
  return (
    <>
      {search("Search activity")}
      <Loadable state={state}>
        {(data) => (
          <>
            <div className="panel"><ActivityList items={data.items} /></div>
            <Pagination page={data.page} pages={data.pages} onChange={setPage} />
          </>
        )}
      </Loadable>
    </>
  );
}
