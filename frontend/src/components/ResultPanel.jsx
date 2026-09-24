const VERDICT_TEXT = {
  AC: "Accepted",
  WA: "Wrong Answer",
  TLE: "Time Limit Exceeded",
  RE: "Runtime Error",
  MLE: "Memory Limit Exceeded",
  OLE: "Output Limit Exceeded",
  IE: "Internal Error",
};

export default function ResultPanel({ result, judging, error }) {
  if (error) return <div className="result-panel"><div className="verdict v-WA">{error}</div></div>;
  if (judging)
    return (
      <div className="result-panel">
        <div className="verdict judging"><span className="spinner" /> Judging in sandbox…</div>
      </div>
    );
  if (!result) return <div className="result-panel muted">Submit karo, result yahan aayega.</div>;

  const d = result.details;
  return (
    <div className="result-panel">
      <div className={`verdict v-${result.verdict}`}>
        {VERDICT_TEXT[result.verdict] || result.verdict}
        <span className="muted small">
          {" "}· {result.passed}/{result.total} passed{result.runtime_ms != null && ` · ${result.runtime_ms}ms`}
        </span>
      </div>
      <div className="test-dots">
        {result.tests?.map((t, i) => (
          <span key={i} className={`tdot t-${t.verdict}`} title={`Test ${i + 1}: ${t.verdict} (${t.time_ms}ms)`} />
        ))}
      </div>
      {result.verdict !== "AC" && <div className="muted small">{result.message}</div>}
      {d && (
        <div className="details">
          <div><div className="label">Input</div><pre>{d.input}</pre></div>
          <div><div className="label">Expected</div><pre>{d.expected}</pre></div>
          {d.got != null && <div><div className="label">Your output</div><pre>{d.got || "(empty)"}</pre></div>}
          {d.stderr && <div className="full"><div className="label">Error</div><pre className="err">{d.stderr}</pre></div>}
        </div>
      )}
    </div>
  );
}
