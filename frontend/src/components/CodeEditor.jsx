// Monaco = wahi editor jo VS Code mein hai.
// Monaco ko app ke saath hi bundle kiya hai (CDN se nahi), taaki slow/blocked internet pe bhi chale.
import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import "monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution"; // C aur C++ dono
import "monaco-editor/esm/vs/basic-languages/java/java.contribution";
import "monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import { LANGUAGES, getLanguage } from "../languages.js";

self.MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });
window.monaco = monaco; // debugging/automated tests ke liye

export function LanguageSelect({ value, onChange, disabled }) {
  const hint = getLanguage(value).hint;
  return (
    <div className="lang-select">
      <select value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled} aria-label="Language">
        {LANGUAGES.map((l) => (
          <option key={l.id} value={l.id}>{l.label}</option>
        ))}
      </select>
      {hint && <span className="muted small">{hint}</span>}
    </div>
  );
}

export default function CodeEditor({ value, onChange, language = "python", readOnly = false }) {
  return (
    <div className="editor-wrap">
      <Editor
        height="100%"
        language={getLanguage(language).monaco}
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? "")}
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          readOnly,
          tabSize: 4,
          automaticLayout: true,
        }}
        loading={<div className="center muted">Loading editor…</div>}
      />
    </div>
  );
}
