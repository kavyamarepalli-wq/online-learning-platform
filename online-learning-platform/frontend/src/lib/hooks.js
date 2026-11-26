import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";

// Loads data from the API. Old data stays visible while the same screen reloads.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: Boolean(path), path });
  const latest = useRef(0);

  const load = useCallback(async () => {
    if (!path) return;
    const ticket = ++latest.current;
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api.get(path);
      if (ticket === latest.current) setState({ data, error: null, loading: false, path });
    } catch (error) {
      if (ticket === latest.current) setState({ data: null, error, loading: false, path });
    }
  }, [path]);

  useEffect(() => {
    load();
    return () => { latest.current += 1; };
  }, [load]);

  const setData = useCallback((update) => {
    setState((s) => ({ ...s, data: typeof update === "function" ? update(s.data) : update }));
  }, []);

  return { ...state, reload: load, setData };
}

// Form values, client-side checks and the field errors returned by the server.
export function useForm(initial, validate) {
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (name, value) => {
    setValues((v) => ({ ...v, [name]: value }));
    setErrors((e) => ({ ...e, [name]: undefined }));
  };

  const bind = (name) => ({
    name,
    value: values[name] ?? "",
    error: errors[name],
    onChange: (event) => set(name, event.target.value),
  });

  const submit = (action) => async (event) => {
    event?.preventDefault();
    if (busy) return;
    setMessage("");
    const found = Object.fromEntries(
      Object.entries(validate ? validate(values) : {}).filter(([, v]) => v));
    setErrors(found);
    if (Object.keys(found).length) {
      setMessage("Please fix the highlighted fields.");
      return;
    }
    setBusy(true);
    try {
      await action(values);
    } catch (error) {
      setErrors(error.fields || {});
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  };

  return { values, setValues, set, bind, errors, message, busy, submit };
}

export function useTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} | LearnSphere` : "LearnSphere";
  }, [title]);
}
