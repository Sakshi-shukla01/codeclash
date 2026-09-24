// Session = logged-in user + ek WebSocket connection jo poori app share karti hai.
// Koi bhi page `subscribe(fn)` karke live events (match_found, battle_end...) sun sakta hai.
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api, getToken, setToken, wsUrl } from "./api.js";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const listeners = useRef(new Set());
  const wsRef = useRef(null);

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      return;
    }
    try {
      setUser(await api("/users/me"));
    } catch {
      setToken(null);
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  // WebSocket: login hote hi connect, disconnect hone pe 2 second baad reconnect
  useEffect(() => {
    if (!user) return;
    let closedByUs = false;
    let retryTimer, pingTimer;

    const connect = () => {
      const ws = new WebSocket(wsUrl(getToken()));
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        pingTimer = setInterval(() => ws.readyState === 1 && ws.send(JSON.stringify({ type: "ping" })), 25000);
      };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        listeners.current.forEach((fn) => fn(msg));
      };
      ws.onclose = () => {
        setConnected(false);
        clearInterval(pingTimer);
        if (!closedByUs) retryTimer = setTimeout(connect, 2000);
      };
    };
    connect();
    return () => {
      closedByUs = true;
      clearTimeout(retryTimer);
      clearInterval(pingTimer);
      wsRef.current?.close();
    };
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const subscribe = useCallback((fn) => {
    listeners.current.add(fn);
    return () => listeners.current.delete(fn);
  }, []);

  const send = useCallback((msg) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === 1) ws.send(JSON.stringify(msg));
  }, []);

  const login = async (username, password) => {
    const data = await api("/auth/login", { method: "POST", body: { username, password } });
    setToken(data.access_token);
    setUser(data.user);
  };

  const signup = async (username, email, password) => {
    const data = await api("/auth/signup", { method: "POST", body: { username, email, password } });
    setToken(data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <SessionContext.Provider
      value={{ user, loading, connected, login, signup, logout, refreshUser, subscribe, send }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => useContext(SessionContext);
