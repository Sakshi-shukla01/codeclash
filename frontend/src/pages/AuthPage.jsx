import { useState } from "react";
import { useSession } from "../session.jsx";

export default function AuthPage() {
  const { login, signup } = useSession();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(form.username, form.password);
      else await signup(form.username, form.email, form.password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-hero">
        <h1>⚔️ CodeClash</h1>
        <p className="muted">Real-time 1v1 coding battles. Same problem, same clock. Solve it first to win.</p>
      </div>
      <form className="card auth-card" onSubmit={submit}>
        <div className="tabs">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button>
          <button type="button" className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")}>Sign up</button>
        </div>
        <label>Username<input value={form.username} onChange={set("username")} required autoFocus /></label>
        {mode === "signup" && (
          <label>Email<input type="email" value={form.email} onChange={set("email")} required /></label>
        )}
        <label>Password<input type="password" value={form.password} onChange={set("password")} required minLength={6} /></label>
        {error && <div className="error">{error}</div>}
        <button className="btn primary" disabled={busy}>
          {busy ? "…" : mode === "login" ? "Login" : "Create account"}
        </button>
      </form>
    </div>
  );
}
