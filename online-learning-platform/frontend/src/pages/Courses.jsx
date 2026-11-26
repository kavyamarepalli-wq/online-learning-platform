import { useEffect, useState } from "react";
import { FiSearch } from "react-icons/fi";
import CourseCard from "../components/CourseCard.jsx";
import { Button, EmptyState, Field, Loadable, Pagination } from "../components/ui.jsx";
import { plural } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { navigate, useQuery } from "../lib/router.jsx";

export default function Courses() {
  useTitle("Courses");
  const query = useQuery();
  const meta = useApi("/meta");
  const state = useApi(`/courses?${query.toString()}`);
  const urlText = query.get("q") || "";
  const [text, setText] = useState(urlText);

  // Filters live in the address bar, so results can be bookmarked and shared.
  const update = (changes, replace = false) => {
    const next = new URLSearchParams(window.location.search);
    if (!("page" in changes)) next.delete("page");
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    const search = next.toString();
    navigate(`/courses${search ? `?${search}` : ""}`, { replace, scroll: "page" in changes });
  };

  useEffect(() => setText(urlText), [urlText]);
  useEffect(() => {
    if (text.trim() === urlText) return undefined;
    const timer = setTimeout(() => update({ q: text.trim() }, true), 350);
    return () => clearTimeout(timer);
  }, [text]);

  const filtered = ["q", "category", "level"].some((k) => query.get(k));

  return (
    <div className="container section">
      <h1>Explore courses</h1>
      <form className="filters" role="search" onSubmit={(e) => { e.preventDefault(); update({ q: text.trim() }); }}>
        <div className="grow search-field">
          <Field label="Search" type="search" value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Title, topic or instructor" />
          <FiSearch aria-hidden="true" />
        </div>
        <Field label="Category" as="select" value={query.get("category") || ""}
          onChange={(e) => update({ category: e.target.value })}>
          <option value="">All categories</option>
          {meta.data?.categories.map((c) => <option key={c}>{c}</option>)}
        </Field>
        <Field label="Level" as="select" value={query.get("level") || ""}
          onChange={(e) => update({ level: e.target.value })}>
          <option value="">All levels</option>
          {meta.data?.levels.map((l) => <option key={l}>{l}</option>)}
        </Field>
        <Field label="Sort by" as="select" value={query.get("sort") || "newest"}
          onChange={(e) => update({ sort: e.target.value })}>
          <option value="newest">Newest</option>
          <option value="popular">Most popular</option>
          <option value="title">Title (A to Z)</option>
        </Field>
      </form>

      <Loadable state={state}>
        {(data) => (
          <div className={state.loading ? "dimmed" : ""}>
            <div className="result-line">
              <span role="status">{plural(data.total, "course")} found</span>
              {filtered && <Button variant="link" onClick={() => { setText(""); navigate("/courses"); }}>Clear filters</Button>}
            </div>
            {data.items.length
              ? <div className="grid">{data.items.map((c) => <CourseCard key={c.id} course={c} />)}</div>
              : <EmptyState title="No courses match" text="Try a different search or clear the filters." />}
            <Pagination page={data.page} pages={data.pages} onChange={(page) => update({ page: String(page) })} />
          </div>
        )}
      </Loadable>
    </div>
  );
}
