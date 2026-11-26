export function formatDate(iso) {
  if (!iso) return "Never";
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function formatDateTime(iso) {
  if (!iso) return "Never";
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

export function formatDuration(seconds) {
  if (!seconds) return "";
  if (seconds < 60) return `${seconds} sec`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min`;
}

export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export const plural = (count, word, many = `${word}s`) => `${count} ${count === 1 ? word : many}`;

export const checks = {
  email: (v) => (/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test((v || "").trim()) ? "" : "Enter a valid email address."),
  password: (v) => {
    if (!v || v.length < 8) return "Password must be at least 8 characters.";
    if (!/[A-Za-z]/.test(v) || !/\d/.test(v)) return "Password must contain at least one letter and one number.";
    return "";
  },
  min: (v, n, label) => ((v || "").trim().length >= n ? "" : `${label} must be at least ${n} characters.`),
};
