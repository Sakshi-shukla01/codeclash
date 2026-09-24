// Monaco = wahi editor jo VS Code mein hai.
// Monaco ko app ke saath hi bundle kiya hai (CDN se nahi), taaki slow/blocked internet pe bhi chale.
import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
import "monaco-editor/esm/vs/basic-languages/python/python.contribution";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";

self.MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });
window.monaco = monaco; // debugging/automated tests ke liye

export const STARTER_CODE = `import sys

def main():
    data = sys.stdin.read().split()
    # apna code yahan likho
    print(data)

main()
`;

export default function CodeEditor({ value, onChange, readOnly = false }) {
  return (
    <div className="editor-wrap">
      <Editor
        height="100%"
        language="python"
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
