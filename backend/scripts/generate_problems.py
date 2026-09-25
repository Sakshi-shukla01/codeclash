"""
Problem set generator.

Har problem ke liye ek reference (sahi) solution hai. Yeh script random test
inputs banati hai, reference solution se expected output nikalti hai, aur sab
kuch `app/seed/problems.json` mein likh deti hai.

Naya problem add karna ho toh:
  1. PROBLEMS list mein ek naya dict add karo (statement + gen + solve)
  2. `python scripts/generate_problems.py` chalao
  3. Backend restart karo (seed sirf naye slugs add karta hai)
"""
import json
import random
from pathlib import Path

rng = random.Random(42)  # fixed seed -> har baar same tests
OUT = Path(__file__).resolve().parent.parent / "app" / "seed" / "problems.json"


# ---------------------------------------------------------------- helpers
def ints(xs):
    return " ".join(map(str, xs))


# ---------------------------------------------------------------- 1. Sum of Two
def sum_gen(big):
    lim = 10**18 if big else 1000
    a, b = rng.randint(-lim, lim), rng.randint(-lim, lim)
    return f"{a} {b}\n"


def sum_solve(inp):
    a, b = map(int, inp.split())
    return str(a + b)


# ---------------------------------------------------------------- 2. Palindrome
def pal_gen(big):
    n = rng.randint(50000, 100000) if big else rng.randint(1, 12)
    half = "".join(rng.choice("abc") for _ in range(n // 2))
    if rng.random() < 0.5:
        s = half + (rng.choice("abc") if n % 2 else "") + half[::-1]
    else:
        s = "".join(rng.choice("abc") for _ in range(n))
    return (s or "a") + "\n"


def pal_solve(inp):
    s = inp.strip()
    return "YES" if s == s[::-1] else "NO"


# ---------------------------------------------------------------- 3. Two Sum
def twosum_gen(big):
    n = 100000 if big else rng.randint(2, 8)
    arr = rng.sample(range(-10**9, 10**9), n) if big else rng.sample(range(-50, 50), n)
    i, j = sorted(rng.sample(range(n), 2))
    target = arr[i] + arr[j]
    # uniqueness: agar koi aur pair bhi target banata hai toh dobara try karo
    seen, count = {}, 0
    for k, x in enumerate(arr):
        count += seen.get(target - x, 0)
        seen[x] = seen.get(x, 0) + 1
    if count != 1:
        return twosum_gen(big)
    return f"{n} {target}\n{ints(arr)}\n"


def twosum_solve(inp):
    data = inp.split()
    n, target = int(data[0]), int(data[1])
    arr = list(map(int, data[2 : 2 + n]))
    pos = {}
    for j, x in enumerate(arr):
        if target - x in pos:
            return f"{pos[target - x]} {j}"
        pos[x] = j
    return "-1 -1"


# ---------------------------------------------------------------- 4. Max Subarray
def kadane_gen(big):
    n = 100000 if big else rng.randint(1, 10)
    lim = 10**9 if big else 20
    return f"{n}\n{ints(rng.randint(-lim, lim) for _ in range(n))}\n"


def kadane_solve(inp):
    data = list(map(int, inp.split()))
    arr = data[1 : 1 + data[0]]
    best = cur = arr[0]
    for x in arr[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return str(best)


# ---------------------------------------------------------------- 5. Valid Brackets
def brackets_gen(big):
    n = rng.randint(50000, 100000) if big else rng.randint(1, 12)
    if rng.random() < 0.5:  # valid bnao
        stack, out = [], []
        pairs = {"(": ")", "[": "]", "{": "}"}
        while len(out) + len(stack) < n:
            if stack and rng.random() < 0.5:
                out.append(pairs[stack.pop()])
            else:
                c = rng.choice("([{")
                stack.append(c)
                out.append(c)
        while stack:
            out.append(pairs[stack.pop()])
        s = "".join(out)
    else:
        s = "".join(rng.choice("()[]{}") for _ in range(n))
    return s + "\n"


def brackets_solve(inp):
    s = inp.strip()
    pairs = {")": "(", "]": "[", "}": "{"}
    st = []
    for c in s:
        if c in "([{":
            st.append(c)
        elif not st or st.pop() != pairs[c]:
            return "NO"
    return "YES" if not st else "NO"


# ---------------------------------------------------------------- 6. Fibonacci mod
MOD = 10**9 + 7


def fib_gen(big):
    return f"{rng.randint(10**5, 10**6) if big else rng.randint(0, 30)}\n"


def fib_solve(inp):
    n = int(inp)
    a, b = 0, 1
    for _ in range(n):
        a, b = b, (a + b) % MOD
    return str(a)


# ---------------------------------------------------------------- 7. Count Primes
def primes_gen(big):
    return f"{rng.randint(5 * 10**5, 10**6) if big else rng.randint(1, 100)}\n"


def primes_solve(inp):
    n = int(inp)
    if n < 2:
        return "0"
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            sieve[i * i :: i] = bytearray(len(range(i * i, n + 1, i)))
    return str(sum(sieve))


# ---------------------------------------------------------------- 8. Anagram
def anagram_gen(big):
    n = 100000 if big else rng.randint(1, 10)
    a = "".join(rng.choice("abcdef") for _ in range(n))
    if rng.random() < 0.5:
        b = "".join(rng.sample(a, len(a)))
    else:
        b = "".join(rng.choice("abcdef") for _ in range(n))
    return f"{a}\n{b}\n"


def anagram_solve(inp):
    a, b = inp.split()
    return "YES" if sorted(a) == sorted(b) else "NO"


# ---------------------------------------------------------------- 9. Second Largest
def second_gen(big):
    n = 100000 if big else rng.randint(1, 8)
    lim = 10**9 if big else 10
    arr = [rng.randint(-lim, lim) for _ in range(n)]
    if not big and rng.random() < 0.2:
        arr = [arr[0]] * n  # sab same -> -1 case
    return f"{n}\n{ints(arr)}\n"


def second_solve(inp):
    data = list(map(int, inp.split()))
    vals = sorted(set(data[1 : 1 + data[0]]), reverse=True)
    return str(vals[1]) if len(vals) > 1 else "NONE"


# ---------------------------------------------------------------- 10. Word Frequency
WORDS = ["code", "clash", "python", "fast", "api", "redis", "docker", "win", "bug", "test"]


def freq_gen(big):
    n = 100000 if big else rng.randint(1, 10)
    return f"{n}\n{' '.join(rng.choice(WORDS) for _ in range(n))}\n"


def freq_solve(inp):
    data = inp.split()
    words = data[1 : 1 + int(data[0])]
    cnt = {}
    for w in words:
        cnt[w] = cnt.get(w, 0) + 1
    best = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return f"{best[0]} {best[1]}"


PROBLEMS = [
    {
        "slug": "sum-of-two",
        "title": "Sum of Two Numbers",
        "difficulty": "easy",
        "gen": sum_gen,
        "solve": sum_solve,
        "description": """Given two integers `a` and `b`, print their sum.

**Input**
A single line containing two integers `a` and `b` (−10^18 ≤ a, b ≤ 10^18).

**Output**
Print `a + b`.""",
    },
    {
        "slug": "palindrome-check",
        "title": "Palindrome Check",
        "difficulty": "easy",
        "gen": pal_gen,
        "solve": pal_solve,
        "description": """Given a string `s` of lowercase English letters, determine whether it reads the same forwards and backwards.

**Input**
A single line containing the string `s` (1 ≤ |s| ≤ 10^5).

**Output**
Print `YES` if `s` is a palindrome, otherwise print `NO`.""",
    },
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "easy",
        "gen": twosum_gen,
        "solve": twosum_solve,
        "description": """Given an array of `n` distinct integers and an integer `target`, find two indices `i < j` such that `a[i] + a[j] = target`. It is guaranteed that exactly one such pair exists.

**Input**
The first line contains `n` and `target` (2 ≤ n ≤ 10^5).
The second line contains `n` integers (0-indexed).

**Output**
Print the two indices `i j` (0-based, i < j).

*Note:* an O(n²) solution will exceed the time limit on large tests.""",
    },
    {
        "slug": "max-subarray-sum",
        "title": "Maximum Subarray Sum",
        "difficulty": "medium",
        "gen": kadane_gen,
        "solve": kadane_solve,
        "description": """Given an array of `n` integers, find the maximum sum of any non-empty contiguous subarray.

**Input**
The first line contains `n` (1 ≤ n ≤ 10^5).
The second line contains `n` integers (|a_i| ≤ 10^9).

**Output**
Print the maximum subarray sum.""",
    },
    {
        "slug": "valid-brackets",
        "title": "Valid Brackets",
        "difficulty": "easy",
        "gen": brackets_gen,
        "solve": brackets_solve,
        "description": """Given a string consisting only of the characters `()[]{}`, determine whether every opening bracket is closed by the same type of bracket in the correct order.

**Input**
A single line containing the string `s` (1 ≤ |s| ≤ 10^5).

**Output**
Print `YES` if the brackets are valid, otherwise print `NO`.""",
    },
    {
        "slug": "fibonacci-mod",
        "title": "Fibonacci Modulo",
        "difficulty": "medium",
        "gen": fib_gen,
        "solve": fib_solve,
        "description": """The Fibonacci sequence is defined as `F(0) = 0`, `F(1) = 1`, and `F(n) = F(n-1) + F(n-2)`. Print `F(n) mod 1000000007`.

**Input**
A single integer `n` (0 ≤ n ≤ 10^6).

**Output**
Print `F(n) mod 1000000007`.

*Note:* a naive recursive solution will exceed the time limit.""",
    },
    {
        "slug": "count-primes",
        "title": "Count Primes",
        "difficulty": "medium",
        "gen": primes_gen,
        "solve": primes_solve,
        "description": """Count the prime numbers between `1` and `n`, inclusive.

**Input**
A single integer `n` (1 ≤ n ≤ 10^6).

**Output**
Print the number of primes in the range [1, n].

*Hint:* consider the Sieve of Eratosthenes.""",
    },
    {
        "slug": "anagram-check",
        "title": "Anagram Check",
        "difficulty": "easy",
        "gen": anagram_gen,
        "solve": anagram_solve,
        "description": """Given two strings `a` and `b`, determine whether `b` is an anagram of `a`, meaning it contains exactly the same letters with the same counts, possibly in a different order.

**Input**
The first line contains `a`. The second line contains `b` (1 ≤ |a|, |b| ≤ 10^5, lowercase letters).

**Output**
Print `YES` if `b` is an anagram of `a`, otherwise print `NO`.""",
    },
    {
        "slug": "second-largest",
        "title": "Second Largest",
        "difficulty": "easy",
        "gen": second_gen,
        "solve": second_solve,
        "description": """Given `n` integers, print the second largest **distinct** value. If it does not exist (all values are equal), print `NONE`.

**Input**
The first line contains `n` (1 ≤ n ≤ 10^5). The second line contains `n` integers.

**Output**
Print the second largest distinct value, or `NONE`.""",
    },
    {
        "slug": "most-frequent-word",
        "title": "Most Frequent Word",
        "difficulty": "easy",
        "gen": freq_gen,
        "solve": freq_solve,
        "description": """Given `n` words, print the word that appears most often, followed by its count. If several words are tied, print the lexicographically smallest one.

**Input**
The first line contains `n` (1 ≤ n ≤ 10^5). The second line contains `n` lowercase words.

**Output**
Print `word count`.""",
    },
]


def main():
    out = []
    for p in PROBLEMS:
        tests = []
        # 2 sample (chhote) + 5 hidden chhote + 2 hidden bade
        for kind in ["sample", "sample"] + ["hidden"] * 5 + ["big", "big"]:
            inp = p["gen"](big=(kind == "big"))
            tests.append(
                {"input": inp, "expected_output": p["solve"](inp) + "\n", "is_sample": kind == "sample"}
            )
        out.append(
            {
                "slug": p["slug"],
                "title": p["title"],
                "difficulty": p["difficulty"],
                "description": p["description"],
                "time_limit_ms": 2000,
                "memory_limit_mb": 256,
                "test_cases": tests,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"Wrote {len(out)} problems -> {OUT}")


if __name__ == "__main__":
    main()
