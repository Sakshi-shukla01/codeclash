import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import CodeEditor, { STARTER_CODE } from "../components/CodeEditor.jsx";
import ProblemView from "../components/ProblemView.jsx";
import ResultPanel from "../components/ResultPanel.jsx";
import { useSession } from "../session.jsx";

const codeKey = (id) => `codeclash_code_match_${id}`;

function loadCode(id) {
  try {
    return localStorage.getItem(codeKey(id)) || STARTER_CODE;
  } catch {
    return STARTER_CODE;
  }
}

function Countdown({ endsAt, stopped }) {
  const [now, setNow] = useState(Date.now() / 1000);
  useEffect(() => {
    if (stopped) return;
    const t = setInterval(() => setNow(Date.now() / 1000), 250);
    return () => clearInterval(t);
  }, [stopped]);
  const left = Math.max(0, Math.round(endsAt - now));
  const urgent = left <= 60;
  return (
    <div className={`countdown ${urgent ? "urgent" : ""}`}>
      ⏱ {Math.floor(left / 60)}:{String(left % 60).padStart(2, "0")}
    </div>
  );
}

function Progress({ label, passed, total, typing, mine }) {
  const pct = total ? (passed / total) * 100 : 0;
  return (
    <div className="progress-box">
      <div className="progress-label">
        <span>{label} {typing && <span className="typing">typing…</span>}</span>
        <span>{passed}/{total}</span>
      </div>
      <div className="bar"><div className={`fill ${mine ? "mine" : "theirs"}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

export default function Battle() {
  const { id } = useParams();
  const matchId = Number(id);
  const navigate = useNavigate();
  const { user, subscribe, send, refreshUser } = useSession();

  const [match, setMatch] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [code, setCode] = useState(() => loadCode(matchId));
  const [myPassed, setMyPassed] = useState(0);
  const [oppPassed, setOppPassed] = useState(0);
  const [oppTyping, setOppTyping] = useState(false);
  const [judging, setJudging] = useState(false);
  const [result, setResult] = useState(null);
  const [submitError, setSubmitError] = useState("");
  const [ending, setEnding] = useState(null); // battle_end event
  const [hideModal, setHideModal] = useState(false);
  const typingTimer = useRef(null);
  const lastTypingSent = useRef(0);

  const load = useCallback(async () => {
    try {
      const m = await api(`/matches/${matchId}`);
      setMatch(m);
      setMyPassed(m.my_passed);
      setOppPassed(m.opponent_passed);
    } catch (e) {
      setLoadError(e.message);
    }
  }, [matchId]);

  useEffect(() => {
    load();
  }, [load]);

  // Live events
  useEffect(
    () =>
      subscribe((msg) => {
        if (msg.match_id !== matchId) return;
        if (msg.type === "submission_result") {
          setJudging(false);
          setResult(msg);
          setMyPassed((p) => Math.max(p, msg.passed));
        } else if (msg.type === "opponent_progress") {
          setOppPassed(msg.passed);
        } else if (msg.type === "opponent_typing") {
          setOppTyping(true);
          clearTimeout(typingTimer.current);
          typingTimer.current = setTimeout(() => setOppTyping(false), 2500);
        } else if (msg.type === "battle_end") {
          setEnding(msg);
          setJudging(false);
          refreshUser();
          load();
        }
      }),
    [subscribe, matchId, load, refreshUser]
  );

  const onCodeChange = (v) => {
    setCode(v);
    try {
      localStorage.setItem(codeKey(matchId), v);
    } catch {
      /* ignore */
    }
    const now = Date.now();
    if (now - lastTypingSent.current > 1500) {
      lastTypingSent.current = now;
      send({ type: "typing", match_id: matchId });
    }
  };

  const submit = async () => {
    setSubmitError("");
    setJudging(true);
    try {
      await api("/submissions", { method: "POST", body: { match_id: matchId, code } });
    } catch (e) {
      setJudging(false);
      setSubmitError(e.message);
    }
  };

  const forfeit = async () => {
    if (!window.confirm("Sach mein haar maan loge? Rating ghategi.")) return;
    await api(`/matches/${matchId}/forfeit`, { method: "POST" }).catch((e) => setSubmitError(e.message));
  };

  if (loadError) return <div className="center error">{loadError}</div>;
  if (!match) return <div className="center muted">Loading battle…</div>;

  const finished = match.status === "finished";
  const iWon = match.winner_id === user.id;
  const change = ending ? ending.rating_change : match.my_rating_change;
  const reasonText = { accepted: "solved it first", timeout: "time up", forfeit: "forfeit" }[
    ending?.reason || match.end_reason
  ];

  return (
    <div className="battle">
      <div className="battle-bar">
        <Progress label={`You (${match.me.username})`} passed={myPassed} total={match.total_tests} mine />
        <Countdown endsAt={match.ends_at} stopped={finished} />
        <Progress
          label={`${match.opponent.username} (${match.opponent.rating})`}
          passed={oppPassed}
          total={match.total_tests}
          typing={oppTyping && !finished}
        />
      </div>

      <div className="battle-body">
        <div className="pane left"><ProblemView problem={match.problem} /></div>
        <div className="pane right">
          <CodeEditor value={code} onChange={onCodeChange} readOnly={finished} />
          <div className="actions">
            <button className="btn primary" onClick={submit} disabled={judging || finished}>
              {judging ? "Judging…" : "Submit ▶"}
            </button>
            {!finished && <button className="btn danger ghost" onClick={forfeit}>Forfeit</button>}
          </div>
          <ResultPanel result={result} judging={judging} error={submitError} />
        </div>
      </div>

      {finished && !hideModal && (
        <div className="modal-backdrop">
          <div className="modal card">
            <div className="big-emoji">{match.is_draw ? "🤝" : iWon ? "🏆" : "💀"}</div>
            <h2>{match.is_draw ? "Draw!" : iWon ? "You won!" : "You lost"}</h2>
            <p className="muted">{reasonText}</p>
            <p className={change >= 0 ? "pos big-num" : "neg big-num"}>
              {change >= 0 ? "+" : ""}{change} rating
            </p>
            <div className="modal-actions">
              <button className="btn primary" onClick={() => navigate("/")}>Back to lobby</button>
              <button className="btn ghost" onClick={() => setHideModal(true)}>View code</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
