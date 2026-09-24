import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import CodeEditor, { STARTER_CODE } from "../components/CodeEditor.jsx";
import ProblemView from "../components/ProblemView.jsx";
import ResultPanel from "../components/ResultPanel.jsx";
import { useSession } from "../session.jsx";

export default function Practice() {
  const { slug } = useParams();
  const { subscribe } = useSession();
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState(STARTER_CODE);
  const [judging, setJudging] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  // Judge bahut fast ho toh result POST ke response se PEHLE aa sakta hai.
  // Isliye results ko id ke hisaab se yaad rakhte hain (refs, taaki stale state ka issue na ho).
  const pendingId = useRef(null);
  const earlyResults = useRef({});

  useEffect(() => {
    setResult(null);
    api(`/problems/${slug}`).then(setProblem).catch((e) => setError(e.message));
  }, [slug]);

  useEffect(
    () =>
      subscribe((msg) => {
        if (msg.type !== "submission_result" || msg.match_id) return;
        if (msg.submission_id === pendingId.current) {
          pendingId.current = null;
          setResult(msg);
          setJudging(false);
        } else {
          earlyResults.current[msg.submission_id] = msg;
        }
      }),
    [subscribe]
  );

  const submit = async () => {
    setError("");
    setResult(null);
    setJudging(true);
    try {
      const sub = await api("/submissions", { method: "POST", body: { problem_slug: slug, code } });
      const early = earlyResults.current[sub.id];
      if (early) {
        setResult(early);
        setJudging(false);
      } else {
        pendingId.current = sub.id;
      }
    } catch (e) {
      setJudging(false);
      setError(e.message);
    }
  };

  if (!problem) return <div className="center muted">{error || "Loading…"}</div>;

  return (
    <div className="battle">
      <div className="battle-bar practice-bar">
        <Link to="/" className="btn ghost small">← Lobby</Link>
        <span className="muted">Practice mode · rating pe koi asar nahi</span>
      </div>
      <div className="battle-body">
        <div className="pane left"><ProblemView problem={problem} /></div>
        <div className="pane right">
          <CodeEditor value={code} onChange={setCode} />
          <div className="actions">
            <button className="btn primary" onClick={submit} disabled={judging}>
              {judging ? "Judging…" : "Submit ▶"}
            </button>
          </div>
          <ResultPanel result={result} judging={judging} error={error} />
        </div>
      </div>
    </div>
  );
}
