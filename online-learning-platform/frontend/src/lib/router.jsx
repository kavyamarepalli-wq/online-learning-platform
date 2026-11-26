// A small history-based router.
import { createContext, useContext, useEffect, useMemo, useState } from "react";

const RouterContext = createContext(null);
const read = () => ({ path: window.location.pathname, search: window.location.search });

export function navigate(to, { replace = false, scroll = true } = {}) {
  window.history[replace ? "replaceState" : "pushState"]({}, "", to);
  window.dispatchEvent(new PopStateEvent("popstate"));
  if (scroll) window.scrollTo(0, 0);
}

export function RouterProvider({ children }) {
  const [location, setLocation] = useState(read);
  useEffect(() => {
    const update = () => setLocation(read());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return <RouterContext.Provider value={location}>{children}</RouterContext.Provider>;
}

export function useLocation() {
  return useContext(RouterContext);
}

export function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

export function matchPath(pattern, path) {
  const wanted = pattern.split("/").filter(Boolean);
  const actual = path.split("/").filter(Boolean);
  if (wanted.length !== actual.length) return null;
  const params = {};
  for (let i = 0; i < wanted.length; i += 1) {
    if (wanted[i].startsWith(":")) params[wanted[i].slice(1)] = decodeURIComponent(actual[i]);
    else if (wanted[i] !== actual[i]) return null;
  }
  return params;
}

export function Link({ to, onClick, children, ...rest }) {
  const handle = (event) => {
    onClick?.(event);
    // Let the browser handle "open in new tab" and similar.
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey
        || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigate(to);
  };
  return <a href={to} onClick={handle} {...rest}>{children}</a>;
}
