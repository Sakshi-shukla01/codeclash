import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api.js";
import { useSession } from "../session.jsx";

function fmt(sec) {
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

export default function Lobby() {
  const { user, subscribe, refreshUser } = useSession();
  const navigate = useNavigate();
  const [queue, setQueue] = useState({ status: "idle" });
  const [waited, setWaited] = useState(0);
  const [leaderboard, setLeaderboard] = useState([]);
  const [history, setHistory] = useState([]);
  const [problems, setProblems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    refreshUser();
    api("/matchmaking/status").then(setQueue).catch(() => {});
    api("/leaderboard").then(setLeaderboard).catch(() => {});
    api(`/users/${user.id}/matches`).then(setHistory).catch(() => {});
    api("/problems").then(setProblems).catch(() => {});
  }, [user.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // match mil gaya -> seedha battle page
  useEffect(
    () => subscribe((msg) => msg.type === "match_found" && navigate(`/battle/${msg.match_id}`)),
    [subscribe, navigate]
  );

  // searching timer
  useEffect(() => {
    if (queue.status !== "searching") return setWaited(0);
    const t = setInterval(() => setWaited((w) => w + 1), 1000);
    return () => clearInterval(t);
  }, [queue.status]);

  const findMatch = async () => {
    setError("");
    try {
      const res = await api("/matchmaking/join", { method: "POST" });
      if (res.status === "in_match") navigate(`/battle/${res.match_id}`);
      else setQueue(res);
    } catch (e) {
      setError(e.message);
    }
  };

  const cancel = async () => {
    await api("/matchmaking/leave", { method: "POST" }).catch(() => {});
    setQueue({ status: "idle" });
  };

  const total = user.wins + user.losses + user.draws;

  return (
    <div className="page lobby">
      <section className="card hero-card">
        <div>
          <h2>Ready to clash, {user.username}?</h2>
          <p className="muted">
            Rating <b>{user.rating}</b> · {user.wins}W {user.losses}L {user.draws}D
            {total > 0 && ` · ${Math.round((user.wins / total) * 100)}% win rate`}
          </p>
        </div>
        {queue.status === "in_match" ? (
          <button className="btn primary big" onClick={() => navigate(`/battle/${queue.match_id}`)}>Rejoin battle ⚔️</button>
        ) : queue.status === "searching" ? (
          <div className="searching">
            <span className="spinner" /> Searching for opponent… {fmt(waited)}
            <button className="btn ghost small" onClick={cancel}>Cancel</button>
          </div>
        ) : (
          <button className="btn primary big" onClick={findMatch}>Find Match ⚔️</button>
        )}
        {error && <div className="error">{error}</div>}
        {queue.status === "searching" && (
          <p className="muted small tip">
            Waiting for another player to join the queue. Matches are made with players of similar rating.
          </p>
        )}
      </section>

      <div className="grid-2">
        <section className="card">
          <h3>🏆 Leaderboard</h3>
          <table>
            <thead><tr><th>#</th><th>Player</th><th>Rating</th><th>W/L/D</th></tr></thead>
            <tbody>
              {leaderboard.map((e) => (
                <tr key={e.id} className={e.id === user.id ? "me" : ""}>
                  <td>{e.rank}</td><td>{e.username}</td><td>{e.rating}</td>
                  <td className="muted">{e.wins}/{e.losses}/{e.draws}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h3>📜 Recent battles</h3>
          {history.length === 0 && <p className="muted">No battles yet. Click Find Match to start your first one.</p>}
          <ul className="history">
            {history.map((m) => (
              <li key={m.id}>
                <Link to={`/battle/${m.id}`}>
                  <span className={`res res-${m.result}`}>{m.result.toUpperCase()}</span>
                  vs <b>{m.opponent}</b> <span className="muted">· {m.problem}</span>
                  {m.result !== "live" && (
                    <span className={m.rating_change >= 0 ? "pos" : "neg"}>
                      {m.rating_change >= 0 ? "+" : ""}{m.rating_change}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="card">
        <h3>🧠 Practice problems</h3>
        <div className="problem-grid">
          {problems.map((p) => (
            <Link key={p.slug} to={`/practice/${p.slug}`} className="problem-tile">
              <span>{p.title}</span>
              <span className={`badge diff-${p.difficulty}`}>{p.difficulty}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
