# CodeClash: Setup Guide (Hinglish) 🇮🇳

Yeh guide step-by-step batati hai ki project apne laptop pe kaise chalana hai, kahan kya badalna hai, aur GitHub/resume pe kaise daalna hai.

---

## PART 1: Ek baar ka setup (sirf pehli baar)

### Step 1: Docker Desktop install karo
- Download: https://www.docker.com/products/docker-desktop/
- **Windows:** install karte waqt **"Use WSL 2"** wala option ON rakhna. Agar WSL error aaye, toh PowerShell (Admin) mein chalao:
  ```powershell
  wsl --install
  ```
  Phir laptop restart karo.
- Install ke baad **Docker Desktop app kholo** aur wait karo jab tak neeche "Engine running" (green) na dikhe.
- Check karo (terminal / PowerShell mein):
  ```bash
  docker --version
  docker compose version
  ```
  Dono version dikhayein toh sahi hai. ✅

> **RAM:** Docker ko kam se kam 4GB RAM chahiye. 8GB laptop pe chalega, bas Chrome ke 50 tabs band kar dena 😄

### Step 2: Git + VS Code install karo
- Git: https://git-scm.com/downloads
- VS Code: https://code.visualstudio.com/

### Step 3: Project unzip karo
`codeclash.zip` ko kisi simple folder mein unzip karo, jaise `C:\projects\codeclash` (path mein spaces na hon toh better).

---

## PART 2: Project chalao (sirf 3 commands) 🚀

Terminal kholo (VS Code mein: `Terminal → New Terminal`) aur project folder mein jao:

```bash
cd C:\projects\codeclash
```

**1. Settings file banao:**
```bash
# Windows (PowerShell / CMD):
copy .env.example .env
# Mac / Linux:
cp .env.example .env
```

**2. Sab kuch start karo:**
```bash
docker compose up --build
```
Pehli baar **5-10 minute** lagenge, kyunki images download hongi. Jab logs mein yeh dikhe, samjho ready hai:
```
backend-1  | ... CodeClash backend ready 🚀
judge-1    | ... judge worker ready (mode=docker), listening on 'judge:queue'
```

**3. Browser mein kholo:** 👉 **http://localhost:3000**

> `sandbox-python-1 exited with code 0` dikhe toh **ghabrao mat**. Uska kaam sirf sandbox image banana hai, bana ke woh band ho jaata hai. Yeh normal hai.

### Khud se battle kaise karein (testing)
1. Chrome mein http://localhost:3000 kholo, account banao (jaise `rahul`).
2. **Incognito window** (Ctrl+Shift+N) ya doosra browser (Edge/Firefox) kholo, doosra account banao (jaise `priya`).
3. Dono mein **Find Match ⚔️** dabao. 2-3 second mein dono battle page pe pahunch jaoge.
4. Ek mein galat code submit karo aur doosre mein progress bar dekho. Phir sahi code submit karo → 🏆

Sum of Two ka sahi code (test ke liye):
```python
a, b = map(int, input().split())
print(a + b)
```

### Band kaise karein
- Terminal mein `Ctrl + C`
- Background mein chalana ho: `docker compose up --build -d`, aur band karna ho: `docker compose down`
- **Poora data delete** (fresh start): `docker compose down -v`

### Useful links (project chalte waqt)
| Link | Kya hai |
|---|---|
| http://localhost:3000 | Website |
| http://localhost:8000/docs | Saari APIs ka interactive documentation (Swagger). Yahan se APIs test kar sakte ho |
| http://localhost:8000/health | Backend, Postgres, Redis ka status |

---

## PART 3: Kahan kya badalna hai ✏️

| Kya | Kahan | Zaroori? |
|---|---|---|
| **JWT_SECRET** | `.env` file. Naya secret banao: `python -c "import secrets; print(secrets.token_hex(32))"` | ✅ Deploy se pehle ZAROOR |
| **Database password** | `.env` → `POSTGRES_PASSWORD` (badla toh `docker compose down -v` karke dobara start karo) | ✅ Deploy se pehle |
| **Battle ka time** | `.env` → `BATTLE_DURATION_SECONDS` (testing ke liye 60 rakh sakte ho) | Optional |
| **GitHub username (CI badge)** | `README.md` ki line 4 → `YOUR_GITHUB_USERNAME` | ✅ |
| **Live URL, demo video, benchmark numbers** | `README.md` mein jahan `TODO` likha hai | ✅ |
| **Apna naam** | `LICENSE` file mein `YOUR NAME` | ✅ |
| **Screenshots** | `docs/screenshots/` mein apne screenshots daalo (same naam se) | Recommended |
| **Naye problems** | `backend/scripts/generate_problems.py` (neeche dekho) | Optional |
| **Submit cooldown, max code length** | `backend/app/core/config.py` | Optional |
| **Sandbox limits (memory, CPU)** | `judge/sandbox.py` → `docker_command()` | Optional |
| **Rating K-factor** | `backend/app/services/elo.py` → `K_FACTOR` | Optional |
| **Matchmaking range** | `backend/app/services/matchmaker.py` → `BASE_RANGE`, `RANGE_STEP` | Optional |
| **Colors / design** | `frontend/src/styles.css` → upar `:root` mein colors | Optional |

**Code badla? Toh dobara build karo:**
```bash
docker compose up --build
```

### Naya problem kaise add karein
1. `backend/scripts/generate_problems.py` kholo.
2. Kisi existing problem ko copy karo (jaise `sum_gen` / `sum_solve`) aur apna `gen` (random input banane wala) aur `solve` (sahi answer dene wala) function likho.
3. `PROBLEMS` list mein naya dict add karo (slug, title, difficulty, description).
4. Chalao:
   ```bash
   cd backend
   python scripts/generate_problems.py
   ```
5. `docker compose up --build`. Naya problem automatically database mein aa jaayega.

---

## PART 4: Development mode (code likhte waqt, fast reload) 🛠️

Jab tum code change kar rahe ho, toh har baar `--build` karna slow hai. Tab yeh karo:

**Terminal 1:** sirf database, redis, aur sandbox image Docker se:
```bash
docker compose up postgres redis sandbox-python
```

**Terminal 2:** backend (auto-reload ke saath):
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

**Terminal 3:** judge worker:
```bash
cd judge
pip install -r requirements.txt
python worker.py
```
(Yeh tumhare laptop ke Docker se sandbox containers banayega.)

**Terminal 4:** frontend (auto-reload):
```bash
cd frontend
npm install
npm run dev
```
Ab kholo 👉 **http://localhost:5173**. Code save karte hi page update ho jaayega.

> Node.js chahiye: https://nodejs.org (LTS version, 20 ya 22)

---

## PART 5: Tests chalana 🧪

```bash
# Backend unit tests (Elo, matchmaking, password, JWT)
cd backend
pytest -q

# Judge tests: checker + sandbox attacks (infinite loop, memory bomb, fork bomb, internet access)
cd judge
pip install -r requirements.txt pytest
pytest -v

# Poori battle end-to-end (project chalte hue):
cd backend
python scripts/e2e_battle.py http://localhost:8000
```

E2E test ka output kuch aisa aayega:
```
✅ signed up rahul_b6ab1d and priya_e63604 (rating 1200)
⚔️  match 1 started: problem 'Fibonacci Modulo', 9 tests
❌ wrong submission -> WA (0/9): WA on sample test #1
👀 opponent saw progress: 0/9
✅ correct submission -> AC (9/9) in 114ms
🏆 winner: rahul_b6ab1d  rating 1200 -> 1216 (+16)
⏰ practice infinite loop -> TLE
🎉 END-TO-END TEST PASSED
```

**Windows pe judge tests:** `JUDGE_MODE=docker` default hai, toh kuch set nahi karna. Bas Docker Desktop chal raha ho aur sandbox image bani ho (`docker compose build sandbox-python`).

---

## PART 6: Common problems aur solutions 🔧

| Problem | Solution |
|---|---|
| `port is already allocated` (5432 / 6379 / 8000 / 3000) | Us port pe kuch aur chal raha hai. Jaise laptop pe alag se Postgres install hai. Use band karo, ya `docker-compose.yml` mein `"5432:5432"` ko `"5433:5432"` kar do |
| Har submission pe **"Internal Error"** | Judge ko sandbox image nahi mili. Chalao `docker compose build sandbox-python` aur logs dekho: `docker compose logs judge` |
| `Cannot connect to the Docker daemon` | Docker Desktop app khula nahi hai. Kholo aur "Engine running" ka wait karo |
| WSL 2 error (Windows) | PowerShell (Admin): `wsl --install` → restart. BIOS mein Virtualization ON hona chahiye |
| Find Match dabaya, kuch nahi hua | Doosra player chahiye! Incognito window mein doosra account banao |
| Code change kiya, website pe nahi dikha | `docker compose up --build` (sirf `up` se naya code nahi aata) |
| Sab kuch reset karna hai | `docker compose down -v` phir `docker compose up --build` |
| Top-right mein green dot ki jagah yellow dot | WebSocket disconnect hai. Backend chal raha hai? `docker compose logs backend` dekho |
| npm install error (dev mode) | Node.js 20+ install karo. `node_modules` delete karke dobara `npm install` karo |

Logs dekhne ke liye:
```bash
docker compose logs -f backend
docker compose logs -f judge
```

---

## PART 7: GitHub pe daalna 📤

```bash
cd codeclash
git init
git add .
git commit -m "CodeClash: real-time 1v1 competitive coding platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/codeclash.git
git push -u origin main
```

- Pehle GitHub pe `codeclash` naam ki **nayi empty repository** banao (README add mat karna).
- Push karte hi **Actions** tab mein CI chalega. 4 jobs green hone chahiye ✅
- `.env` push **nahi** hogi (`.gitignore` mein hai). Yeh sahi hai.
- Repo ke "About" section mein description aur topics daalo: `fastapi`, `websocket`, `docker`, `redis`, `online-judge`, `react`

---

## PART 8: Online deploy (free) 🌐

Is project mein judge Docker containers chalata hai, isliye Render/Vercel jaisi hosting kaam nahi karegi. Tumhe ek **VM (virtual server)** chahiye.

**Oracle Cloud Always Free (recommended):**
1. https://www.oracle.com/cloud/free/ pe account banao (card sirf verification ke liye lagta hai).
2. **Sabse pehle Budget alert set karo:** Billing → Budgets → Create (jaise ₹1), taaki galti se charge na ho.
3. Compute → Create Instance → **Ampere A1 (ARM)**, Ubuntu 22.04, "Always Free eligible" wala shape.
4. Networking mein **port 80** open karo (Security List → Ingress rule → port 80).
5. SSH karke server pe:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
   sudo usermod -aG docker $USER && newgrp docker
   git clone https://github.com/YOUR_USERNAME/codeclash.git && cd codeclash
   cp .env.example .env
   nano .env        # JWT_SECRET aur POSTGRES_PASSWORD badlo!
   ```
6. `docker-compose.yml` mein frontend ka port `"3000:80"` → `"80:80"` karo, aur postgres/redis ke `ports:` hata do (bahar se access band, zyada secure).
7. `docker compose up --build -d`
8. Browser: `http://<server-ip>`. Yeh link resume pe daalo 🎉

> ARM server pe bhi sab images kaam karti hain (python, postgres, redis, nginx, node sab multi-arch hain).
> Free domain + HTTPS chahiye toh baad mein Caddy ya Cloudflare Tunnel laga sakte ho.

---

## PART 9: Real users aur resume numbers 📊

1. **College contest karao:** WhatsApp group mein link bhejo, "CodeClash Friday. Top 3 ko treat!" 😄
2. **Load test** karke numbers nikalo:
   ```bash
   pip install locust
   locust -f loadtest/locustfile.py --host http://localhost:8000
   ```
   http://localhost:8089 kholo → 100 users, spawn rate 10 → Start. Requests/sec aur p95 latency note karo.
3. `docker compose up -d --scale judge=4` karke judge throughput 1 worker vs 4 workers compare karo. Yeh horizontal scaling ka proof hai.
4. Yeh numbers README ki table mein aur resume mein daalo.

**Resume bullets (apne real numbers daalna):**
> **CodeClash: Real-time Competitive Coding Platform** | FastAPI, WebSockets, Docker, Redis, PostgreSQL, React | [Live] [GitHub]
> - Built a real-time 1v1 coding battle platform with **Docker-sandboxed execution** of untrusted code (no network, cgroup memory/CPU/PID limits, read-only FS, non-root), verified by automated attack tests in CI.
> - Designed an async judging pipeline (Redis queue → horizontally scalable workers → WebSocket push), handling **X submissions/min** at **Y ms** p95 verdict latency.
> - Implemented rating-based matchmaking, Elo ratings, and cross-instance real-time events via Redis Pub/Sub. **Used by N students** in college contests.

---

## PART 10: Interview ke liye: kaunsi file kya karti hai 🎤

Interview se pehle yeh files ek baar dhyan se padh lena. Har file mein Hinglish comments hain.

| Sawal | File |
|---|---|
| "Code safely kaise chalaya?" | `judge/sandbox.py` (saari docker flags explained) + `judge/sandbox/python/runner.py` |
| "Verdict kaise decide hota hai?" | `judge/checker.py` |
| "Queue kaise kaam karti hai?" | `judge/worker.py` + `backend/app/services/judge_client.py` |
| "Matchmaking?" | `backend/app/services/matchmaker.py` (`find_pairs` function) |
| "Do log ek saath jeetein toh?" | `backend/app/services/battle_manager.py` → `finish_match()` (Redis `SET NX`) |
| "WebSocket multiple servers pe?" | `backend/app/services/events.py` (Redis Pub/Sub) |
| "Elo rating?" | `backend/app/services/elo.py` |
| "Auth kaise kiya?" | `backend/app/core/security.py` (bcrypt + JWT) + `core/deps.py` |
| "Database design?" | `backend/app/models/` |
| "Testing kaise ki?" | `judge/tests/test_sandbox_attacks.py`, `backend/tests/`, `backend/scripts/e2e_battle.py`, `.github/workflows/ci.yml` |

**Honest rehna:** interview mein har cheez apne shabdon mein explain kar pao, isliye har file khud padho, chhote changes karke dekho (jaise memory limit 128MB karo aur memory bomb test chalao), aur samjho ki kyun kaam karta hai. Jo cheez tum samjha nahi sakte, woh resume pe mat likho.

All the best! ⚔️🔥
