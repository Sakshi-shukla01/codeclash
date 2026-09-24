// Problem statement dikhata hai. Chhota sa markdown renderer: **bold**, *italic*, `code`.
// (dangerouslySetInnerHTML use nahi kiya -> XSS ka risk nahi)
function renderInline(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("`") && p.endsWith("`")) return <code key={i}>{p.slice(1, -1)}</code>;
    if (p.startsWith("*") && p.endsWith("*") && p.length > 2) return <em key={i}>{p.slice(1, -1)}</em>;
    return p;
  });
}

export default function ProblemView({ problem }) {
  const paragraphs = problem.description.split(/\n\s*\n/);
  return (
    <div className="problem">
      <div className="problem-head">
        <h2>{problem.title}</h2>
        <span className={`badge diff-${problem.difficulty}`}>{problem.difficulty}</span>
      </div>
      <div className="limits muted">
        ⏱ {problem.time_limit_ms / 1000}s · 💾 {problem.memory_limit_mb}MB · 🐍 Python 3
      </div>
      {paragraphs.map((para, i) => (
        <p key={i}>
          {para.split("\n").map((line, j) => (
            <span key={j}>
              {j > 0 && <br />}
              {renderInline(line)}
            </span>
          ))}
        </p>
      ))}
      {problem.samples.map((s, i) => (
        <div className="sample" key={i}>
          <div>
            <div className="label">Sample input {i + 1}</div>
            <pre>{s.input}</pre>
          </div>
          <div>
            <div className="label">Sample output {i + 1}</div>
            <pre>{s.expected_output}</pre>
          </div>
        </div>
      ))}
    </div>
  );
}
