import { Link } from "react-router-dom";
import { useSession } from "../session.jsx";

export default function Navbar() {
  const { user, logout, connected } = useSession();
  return (
    <nav className="navbar">
      <Link to="/" className="brand">⚔️ CodeClash</Link>
      <div className="nav-right">
        <span className={`dot ${connected ? "online" : "offline"}`} title={connected ? "Live" : "Reconnecting…"} />
        <span className="nav-user">
          {user.username} <span className="rating-chip">{user.rating}</span>
        </span>
        <button className="btn ghost small" onClick={logout}>Logout</button>
      </div>
    </nav>
  );
}
