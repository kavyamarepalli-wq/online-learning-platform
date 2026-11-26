import { useState } from "react";
import { FiCheckCircle } from "react-icons/fi";
import { Alert, Button, Field, Spinner } from "../components/ui.jsx";
import { formatDate } from "../lib/format.js";
import { useApi, useTitle } from "../lib/hooks.js";
import { navigate } from "../lib/router.jsx";

export default function Verify({ params }) {
  useTitle("Verify certificate");
  const [code, setCode] = useState(params.code || "");
  const [error, setError] = useState("");
  const state = useApi(params.code ? `/certificates/verify/${encodeURIComponent(params.code)}` : null);
  const certificate = state.data?.certificate;

  const submit = (event) => {
    event.preventDefault();
    if (!code.trim()) return setError("Enter the certificate ID.");
    navigate(`/verify/${encodeURIComponent(code.trim().toUpperCase())}`);
  };

  return (
    <div className="auth-page">
      <div className="panel auth-card">
        <h1>Verify a certificate</h1>
        <p>Enter the ID printed at the bottom of a LearnSphere certificate.</p>
        <form onSubmit={submit} noValidate>
          <Field label="Certificate ID" value={code} error={error} placeholder="LS-XXXX-XXXX-XXXX"
            onChange={(e) => { setCode(e.target.value); setError(""); }} />
          <Button type="submit" className="btn-block">Verify</Button>
        </form>
        {params.code && state.loading && <Spinner label="Checking..." />}
        {state.error && <Alert type="error">{state.error.message}</Alert>}
        {certificate && !state.loading && (
          <div className="verified" role="status">
            <FiCheckCircle aria-hidden="true" />
            <h2>Valid certificate</h2>
            <dl>
              <dt>Awarded to</dt><dd>{certificate.student_name}</dd>
              <dt>Course</dt><dd>{certificate.course_title}</dd>
              <dt>Instructor</dt><dd>{certificate.instructor_name}</dd>
              <dt>Issued on</dt><dd>{formatDate(certificate.issued_at)}</dd>
              <dt>ID</dt><dd>{certificate.code}</dd>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}
