// Supported languages. `id` backend ko jaata hai, `monaco` editor ki syntax highlighting ke liye hai.
// Naya language add karna ho toh: yahan entry + judge/sandbox/python/runner.py ke LANGUAGES mein entry
// + backend/app/schemas/__init__.py ke SubmitRequest.language mein naam.
export const LANGUAGES = [
  {
    id: "python",
    label: "Python 3",
    monaco: "python",
    starter: `import sys

def main():
    data = sys.stdin.read().split()
    # write your solution here


main()
`,
  },
  {
    id: "cpp",
    label: "C++ 17",
    monaco: "cpp",
    starter: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // write your solution here

    return 0;
}
`,
  },
  {
    id: "java",
    label: "Java",
    monaco: "java",
    hint: "The public class must be named Main.",
    starter: `import java.util.*;
import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringTokenizer st = new StringTokenizer(br.readLine());

        // write your solution here
    }
}
`,
  },
  {
    id: "javascript",
    label: "JavaScript",
    monaco: "javascript",
    starter: `const input = require("fs").readFileSync(0, "utf8").trim().split(/\\s+/);

// write your solution here
`,
  },
  {
    id: "c",
    label: "C",
    monaco: "c",
    starter: `#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    // write your solution here

    return 0;
}
`,
  },
];

export const DEFAULT_LANGUAGE = "python";

export const getLanguage = (id) => LANGUAGES.find((l) => l.id === id) || LANGUAGES[0];

// Aakhri baar chuni gayi language yaad rakho
const LANG_KEY = "codeclash_language";

export function loadPreferredLanguage() {
  try {
    const id = localStorage.getItem(LANG_KEY);
    return LANGUAGES.some((l) => l.id === id) ? id : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

export function savePreferredLanguage(id) {
  try {
    localStorage.setItem(LANG_KEY, id);
  } catch {
    /* ignore */
  }
}

// Har problem/match + language ka code alag save hota hai (language badlo toh code khoye nahi)
export function loadCode(scope, langId) {
  try {
    return localStorage.getItem(`codeclash_code_${scope}_${langId}`) ?? getLanguage(langId).starter;
  } catch {
    return getLanguage(langId).starter;
  }
}

export function saveCode(scope, langId, code) {
  try {
    localStorage.setItem(`codeclash_code_${scope}_${langId}`, code);
  } catch {
    /* ignore */
  }
}
