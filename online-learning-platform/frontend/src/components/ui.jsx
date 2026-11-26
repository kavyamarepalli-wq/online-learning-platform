// Reusable interface pieces: buttons, form fields, messages, dialogs and tables.
import { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from "react";
import { FiAlertCircle, FiCheckCircle, FiChevronLeft, FiChevronRight, FiInbox, FiX } from "react-icons/fi";

export function Button({ variant = "primary", size, busy, children, className = "", disabled, ...rest }) {
  const classes = ["btn", `btn-${variant}`, size ? `btn-${size}` : "", className].join(" ");
  return (
    <button type="button" className={classes} disabled={disabled || busy} aria-busy={busy || undefined} {...rest}>
      {busy && <span className="btn-spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function Field({ label, error, hint, as = "input", children, ...props }) {
  const id = useId();
  const Control = as;
  return (
    <div className={`field ${error ? "has-error" : ""}`}>
      <label htmlFor={id}>{label}</label>
      <Control id={id} aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? `${id}-help` : undefined} {...props}>
        {children}
      </Control>
      {(error || hint) && (
        <small id={`${id}-help`} className={error ? "error-text" : "hint"}>{error || hint}</small>
      )}
    </div>
  );
}

export function Alert({ type = "info", children }) {
  if (!children) return null;
  const Icon = type === "success" ? FiCheckCircle : FiAlertCircle;
  return (
    <div className={`alert alert-${type}`} role={type === "error" ? "alert" : "status"}>
      <Icon aria-hidden="true" /> <span>{children}</span>
    </div>
  );
}

export function Spinner({ label = "Loading..." }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 6000);
    return () => clearTimeout(timer);
  }, []);
  return (
    <div className="spinner-wrap" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
      {slow && <small>The server may be waking up. This can take about a minute on free hosting.</small>}
    </div>
  );
}

// Shows the loading or error state of a useApi() result, then renders the data.
export function Loadable({ state, children }) {
  if (state.error) {
    return (
      <div className="load-error">
        <Alert type="error">{state.error.message}</Alert>
        <Button variant="outline" onClick={state.reload}>Try again</Button>
      </div>
    );
  }
  if (!state.data) return <Spinner />;
  return children(state.data);
}

export function EmptyState({ title, text, children }) {
  return (
    <div className="empty">
      <FiInbox aria-hidden="true" className="empty-icon" />
      <h3>{title}</h3>
      {text && <p>{text}</p>}
      {children}
    </div>
  );
}

export function ProgressBar({ value, label }) {
  return (
    <div className="progress-row">
      <div className="progress" role="progressbar" aria-valuenow={value} aria-valuemin={0}
        aria-valuemax={100} aria-label={label || "Course progress"}>
        <span className={value >= 100 ? "done" : ""} style={{ width: `${value}%` }} />
      </div>
      <strong>{value}%</strong>
    </div>
  );
}

export function Badge({ tone = "neutral", children }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Stat({ icon: Icon, value, label }) {
  return (
    <div className="stat">
      {Icon && <span className="stat-icon"><Icon aria-hidden="true" /></span>}
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

export function Tabs({ tabs, active, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map(([key, label]) => (
        <button key={key} type="button" role="tab" aria-selected={active === key}
          className={active === key ? "active" : ""} onClick={() => onChange(key)}>
          {label}
        </button>
      ))}
    </div>
  );
}

// columns: [header, (row) => cell]. On phones each row becomes a card.
export function Table({ columns, rows, rowKey = "id", empty = "Nothing to show yet." }) {
  if (!rows.length) return <EmptyState title={empty} />;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{columns.map(([h]) => <th key={h} scope="col">{h}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]}>
              {columns.map(([h, cell]) => <td key={h} data-label={h}><div>{cell(row)}</div></td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({ page, pages, onChange }) {
  if (pages <= 1) return null;
  return (
    <nav className="pagination" aria-label="Pages">
      <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        <FiChevronLeft aria-hidden="true" /> Previous
      </Button>
      <span>Page {page} of {pages}</span>
      <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Next <FiChevronRight aria-hidden="true" />
      </Button>
    </nav>
  );
}

export function Modal({ title, onClose, children, wide }) {
  const ref = useRef(null);
  useEffect(() => {
    // The native dialog traps focus and handles the Escape key.
    if (!ref.current.open) ref.current.showModal();
    document.body.classList.add("no-scroll");
    return () => document.body.classList.remove("no-scroll");
  }, []);
  return (
    <dialog ref={ref} className={`modal ${wide ? "wide" : ""}`} aria-label={title}
      onCancel={(e) => { e.preventDefault(); onClose(); }}>
      <header>
        <h2>{title}</h2>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><FiX /></button>
      </header>
      <div className="modal-body">{children}</div>
    </dialog>
  );
}

const ToastContext = createContext(null);
export const useToast = () => useContext(ToastContext);

// Also provides confirm(), a styled replacement for window.confirm.
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const [question, setQuestion] = useState(null);
  const counter = useRef(0);

  const show = useCallback((message, type) => {
    const id = ++counter.current;
    setToasts((list) => [...list, { id, message, type }]);
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 5000);
  }, []);

  const [value] = useState(() => ({}));
  value.success = (message) => show(message, "success");
  value.error = (message) => show(message, "error");
  value.confirm = (options) => new Promise((resolve) => setQuestion({ ...options, resolve }));

  const answer = (result) => {
    question.resolve(result);
    setQuestion(null);
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => <Alert key={t.id} type={t.type}>{t.message}</Alert>)}
      </div>
      {question && (
        <Modal title={question.title} onClose={() => answer(false)}>
          <p>{question.text}</p>
          <div className="actions end">
            <Button variant="outline" onClick={() => answer(false)}>Cancel</Button>
            <Button variant={question.danger ? "danger" : "primary"} onClick={() => answer(true)}>
              {question.action || "Confirm"}
            </Button>
          </div>
        </Modal>
      )}
    </ToastContext.Provider>
  );
}
