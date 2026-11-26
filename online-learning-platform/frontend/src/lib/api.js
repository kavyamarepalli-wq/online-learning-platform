/* global __API_URL__ */
// Every call to the backend goes through this file.
const BASE = `${__API_URL__}/api`;
const TOKEN_KEY = "learnsphere.token";
let memoryToken = null;
let onSessionExpired = () => {};

export const tokenStore = {
  get() {
    try { return localStorage.getItem(TOKEN_KEY) || memoryToken; } catch { return memoryToken; }
  },
  set(token) {
    memoryToken = token;
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token);
      else localStorage.removeItem(TOKEN_KEY);
    } catch { /* private mode: keep the token in memory only */ }
  },
};

export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler;
}

export class ApiError extends Error {
  constructor(message, status, fields = {}) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

function toError(status, body, token) {
  if (status === 401 && token) onSessionExpired(token);
  return new ApiError(body?.error || `Request failed (${status}).`, status, body?.fields);
}

const OFFLINE = "Cannot reach the server. Check your connection and try again.";

async function send(path, { method = "GET", body, keepalive } = {}) {
  const token = tokenStore.get();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let response;
  try {
    response = await fetch(BASE + path, {
      method, headers, keepalive, body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(OFFLINE, 0);
  }
  if (!response.ok) throw toError(response.status, await response.json().catch(() => null), token);
  return response;
}

export const api = {
  get: (path) => send(path).then((r) => r.json()),
  post: (path, body = {}) => send(path, { method: "POST", body }).then((r) => r.json()),
  put: (path, body = {}, options = {}) =>
    send(path, { method: "PUT", body, ...options }).then((r) => r.json()),
  delete: (path) => send(path, { method: "DELETE" }).then((r) => r.json()),

  // Multipart upload with progress (fetch cannot report upload progress).
  upload(path, formData, { method = "POST", onProgress } = {}) {
    return new Promise((resolve, reject) => {
      const token = tokenStore.get();
      const xhr = new XMLHttpRequest();
      xhr.open(method, BASE + path);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      };
      xhr.onload = () => {
        let body = null;
        try { body = JSON.parse(xhr.responseText); } catch { /* not JSON */ }
        if (xhr.status >= 200 && xhr.status < 300) resolve(body);
        else reject(toError(xhr.status, body, token));
      };
      xhr.onerror = () => reject(new ApiError(OFFLINE, 0));
      xhr.send(formData);
    });
  },

  // Downloads a protected file and hands it to the browser.
  async download(path, filename) {
    const blob = await (await send(path)).blob();
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement("a"), { href: url, download: filename });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  },
};
