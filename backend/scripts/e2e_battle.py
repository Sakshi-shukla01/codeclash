"""
End-to-end test: do fake players banake poori battle chalata hai.

  signup x2 -> WebSocket connect -> matchmaking -> match_found
  -> Player A galat code bhejta hai (WA) -> B ko opponent_progress milta hai
  -> Player A sahi code bhejta hai (AC) -> dono ko battle_end + rating change

Chalao (backend + judge worker chalne chahiye):
    python scripts/e2e_battle.py                  # default http://localhost:8000
    python scripts/e2e_battle.py http://localhost:3000   # nginx (docker compose) ke through
"""
import asyncio
import json
import sys
import uuid

import httpx
import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
WS_BASE = BASE.replace("http", "ws", 1)

# Har problem ka sahi solution (e2e test ke liye)
SOLUTIONS = {
    "sum-of-two": "a,b=map(int,input().split())\nprint(a+b)",
    "palindrome-check": "s=input().strip()\nprint('YES' if s==s[::-1] else 'NO')",
    "two-sum": (
        "import sys\nd=sys.stdin.read().split()\nn,t=int(d[0]),int(d[1])\na=list(map(int,d[2:2+n]))\n"
        "p={}\nfor j,x in enumerate(a):\n    if t-x in p:\n        print(p[t-x],j);break\n    p[x]=j"
    ),
    "max-subarray-sum": (
        "import sys\nd=list(map(int,sys.stdin.read().split()))\na=d[1:1+d[0]]\nb=c=a[0]\n"
        "for x in a[1:]:\n    c=max(x,c+x);b=max(b,c)\nprint(b)"
    ),
    "valid-brackets": (
        "s=input().strip()\nm={')':'(',']':'[','}':'{'}\nst=[]\nok=True\nfor ch in s:\n"
        "    if ch in '([{': st.append(ch)\n    elif not st or st.pop()!=m[ch]: ok=False;break\n"
        "print('YES' if ok and not st else 'NO')"
    ),
    "fibonacci-mod": "n=int(input())\na,b=0,1\nfor _ in range(n): a,b=b,(a+b)%1000000007\nprint(a)",
    "count-primes": (
        "n=int(input())\nif n<2: print(0)\nelse:\n    s=bytearray([1])*(n+1);s[0]=s[1]=0\n"
        "    for i in range(2,int(n**.5)+1):\n        if s[i]: s[i*i::i]=bytearray(len(range(i*i,n+1,i)))\n"
        "    print(sum(s))"
    ),
    "anagram-check": "a=input().strip();b=input().strip()\nprint('YES' if sorted(a)==sorted(b) else 'NO')",
    "second-largest": (
        "import sys\nd=list(map(int,sys.stdin.read().split()))\nv=sorted(set(d[1:1+d[0]]),reverse=True)\n"
        "print(v[1] if len(v)>1 else 'NONE')"
    ),
    "most-frequent-word": (
        "import sys\nfrom collections import Counter\nd=sys.stdin.read().split()\nc=Counter(d[1:1+int(d[0])])\n"
        "w=min(c,key=lambda k:(-c[k],k))\nprint(w,c[w])"
    ),
}


async def wait_for(ws, event_type, timeout=60):
    async def _loop():
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == event_type:
                return msg
    return await asyncio.wait_for(_loop(), timeout)


async def main():
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as http:
        players = []
        for name in ("rahul", "priya"):
            uname = f"{name}_{uuid.uuid4().hex[:6]}"
            r = await http.post("/api/v1/auth/signup",
                                json={"username": uname, "email": f"{uname}@test.dev", "password": "secret123"})
            r.raise_for_status()
            data = r.json()
            players.append({"name": uname, "token": data["access_token"], "id": data["user"]["id"],
                            "rating": data["user"]["rating"]})
        a, b = players
        print(f"✅ signed up {a['name']} and {b['name']} (rating {a['rating']})")

        ws_a = await websockets.connect(f"{WS_BASE}/ws?token={a['token']}")
        ws_b = await websockets.connect(f"{WS_BASE}/ws?token={b['token']}")
        hdr = lambda p: {"Authorization": f"Bearer {p['token']}"}  # noqa: E731

        for p in players:
            r = await http.post("/api/v1/matchmaking/join", headers=hdr(p))
            r.raise_for_status()
        print("⏳ both players in queue...")
        found_a, found_b = await asyncio.gather(wait_for(ws_a, "match_found"), wait_for(ws_b, "match_found"))
        assert found_a["match_id"] == found_b["match_id"]
        match_id = found_a["match_id"]

        state = (await http.get(f"/api/v1/matches/{match_id}", headers=hdr(a))).json()
        slug = state["problem"]["slug"]
        print(f"⚔️  match {match_id} started: problem '{state['problem']['title']}', {state['total_tests']} tests, "
              f"opponent={state['opponent']['username']}")

        # 1) galat code
        r = await http.post("/api/v1/submissions", headers=hdr(a),
                            json={"match_id": match_id, "code": "print('wrong')"})
        assert r.status_code == 202, r.text
        res = await wait_for(ws_a, "submission_result")
        prog = await wait_for(ws_b, "opponent_progress")
        print(f"❌ wrong submission -> {res['verdict']} ({res['passed']}/{res['total']}): {res['message']}")
        print(f"👀 opponent saw progress: {prog['passed']}/{prog['total']}")
        assert res["verdict"] == "WA"

        await asyncio.sleep(3.2)  # submit cooldown

        # 2) sahi code
        r = await http.post("/api/v1/submissions", headers=hdr(a),
                            json={"match_id": match_id, "code": SOLUTIONS[slug]})
        assert r.status_code == 202, r.text
        res = await wait_for(ws_a, "submission_result")
        print(f"✅ correct submission -> {res['verdict']} ({res['passed']}/{res['total']}) in {res['runtime_ms']}ms")
        assert res["verdict"] == "AC", res

        end_a, end_b = await asyncio.gather(wait_for(ws_a, "battle_end"), wait_for(ws_b, "battle_end"))
        assert end_a["winner_id"] == a["id"]
        print(f"🏆 winner: {a['name']}  rating {a['rating']} -> {end_a['new_rating']} ({end_a['rating_change']:+d})")
        print(f"😢 loser:  {b['name']}  rating {b['rating']} -> {end_b['new_rating']} ({end_b['rating_change']:+d})")

        # 3) practice mode: infinite loop -> TLE
        r = await http.post("/api/v1/submissions", headers=hdr(b),
                            json={"problem_slug": "sum-of-two", "code": "while True: pass"})
        assert r.status_code == 202, r.text
        res = await wait_for(ws_b, "submission_result")
        print(f"⏰ practice infinite loop -> {res['verdict']}: {res['message']}")
        assert res["verdict"] == "TLE"

        board = (await http.get("/api/v1/leaderboard")).json()
        print(f"📊 leaderboard top: {[(e['username'], e['rating']) for e in board[:3]]}")
        await ws_a.close()
        await ws_b.close()
        print("\n🎉 END-TO-END TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())
