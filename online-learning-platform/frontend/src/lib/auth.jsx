import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, setSessionExpiredHandler, tokenStore } from "./api.js";
import { navigate } from "./router.jsx";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function homeFor(user) {
  if (user?.role === "admin") return "/admin";
  if (user?.role === "instructor") return "/instructor";
  return "/dashboard";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(!tokenStore.get());
  const [problem, setProblem] = useState("");

  const restore = useCallback(async () => {
    if (!tokenStore.get()) return setReady(true);
    setProblem("");
    try {
      setUser((await api.get("/auth/me")).user);
      setReady(true);
    } catch (error) {
      // Keep the token if the server is merely unreachable.
      if (error.status === 401) {
        tokenStore.set(null);
        setReady(true);
      } else {
        setProblem(error.message);
      }
    }
  }, []);

  useEffect(() => {
    setSessionExpiredHandler((failedToken) => {
      if (tokenStore.get() !== failedToken) return;
      tokenStore.set(null);
      setUser(null);
      setReady(true);
    });
    restore();
  }, [restore]);

  const value = useMemo(() => ({
    user,
    ready,
    problem,
    retry: restore,
    signIn(session) {
      tokenStore.set(session.token);
      setUser(session.user);
    },
    updateUser: setUser,
    signOut() {
      tokenStore.set(null);
      setUser(null);
      navigate("/");
    },
  }), [user, ready, problem, restore]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
