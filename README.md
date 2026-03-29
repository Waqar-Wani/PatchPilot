# PatchPilot 🚀🛠️

PatchPilot is a full-stack dashboard that lets you paste any public GitHub repo and have an AI make a safe, small contribution, open a PR, and show live progress. It also checks for README gaps and possible secret leaks, dropping findings into `SECURITY_FINDINGS.md`. (Yes, even the mysterious **dfds** use‑case is covered. 😉)

## At-a-glance 📊
- 🖥️ UI: Dashboard, live logs, stats page (/stats) with cost/tokens/lines changed, severity, PR links.
- 🤖 Agent flow: Snapshot ➜ LLM plan ➜ Safety gates ➜ Git patch ➜ PR ➜ Metrics.
- 🔐 Safety: Delete whitelist, non-empty-content checks, fork fallback if no push rights, secret remediation with SECURITY_FINDINGS.md.
- 🧾 Docs-first: If a repo has no README, PatchPilot will craft a concise README with purpose, features, and quickstart.

## Features ✨
- 📡 Paste a repo URL and kick off an AI-driven contribution job.
- 🧠 Snapshot + analysis to propose docs/tests or security findings.
- 🔀 Auto-branch, patch, push, and open a PR (GitHub API).
- 📺 Live job/status/logs in a modern React UI with animations.
- 🧹 Delete completed jobs from the UI.
- 🔒 Secret/misconfig detection summary in `SECURITY_FINDINGS.md`.
- 📈 Stats page with pagination: success/skip/fail counts, cost per fix, tokens, severity, files/lines changed, PR links.

## Tech Stack 🧰
- Frontend: React + Vite, React Router, Framer Motion, Axios.
- Backend: FastAPI, Celery, MongoDB Atlas, Redis, GitPython, PyGithub.
- AI: OpenRouter (OpenAI-compatible) models.

## Prereqs ⚙️
- Python 3.10+ and Node 18+
- MongoDB Atlas URI
- Redis instance (rediss supported)
- GitHub Personal Access Token
- OpenRouter API key

## Setup 🪛
```bash
git clone https://github.com/Waqar-Wani/PatchPilot
cd patchpilot
```
Fill `./.env` (example):
```
GITHUB_TOKEN=...
MONGO_URI=...
REDIS_URL=...
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=deepseek/deepseek-chat
OPENROUTER_BASE=https://openrouter.ai/api/v1
CLONE_DIR=/tmp/patchpilot_repos
```

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### Worker
```bash
cd backend
source .venv/bin/activate
celery -A celery_app worker --loglevel=info --pool=solo
```

### Frontend
```bash
cd frontend
npm install
npm run dev   # defaults to http://127.0.0.1:5174
```

## How it works (infographic-style) 🧭
1) 📥 Scan: read README (if present), key files, file tree, issues; build snapshot.
2) 🧠 Analyze: LLM proposes the smallest safe fix (docs/tests/security).
3) 🛡️ Validate: evidence gate, delete whitelist, non-empty content, branch defaults.
4) 🔀 Apply: fork if no push rights; commit and push branch; open PR.
5) 📊 Measure: log tokens, cost, files/lines, severity, PR URL to `/api/stats` (shown in UI Stats).

## Usage 🖱️
1. Open the UI at `http://127.0.0.1:5174`.
2. Paste a repo URL you own (start with a test repo).
3. Watch status/logs update live; a PR link appears when done.
4. Use the Delete action to clean old jobs.

## Deployment 🌐
- API: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Worker: `celery -A celery_app worker --loglevel=info`
- Frontend: `npm run build` → deploy `dist/` to static hosting.
- Remember to set `allow_origins` in `backend/main.py` to your prod frontend URL.

## Notes 📓
- Runs minimal, low-risk changes (docs/tests/security summaries).
- Skips only on hard blockers (no access/binary-only). Otherwise, it prefers a small contribution.
- dfds: Done For Developer Sanity—tiny, friendly PRs instead of giant refactors. 😅

## Known issues for testing
- README lacked a quickstart example (now addressed).
- Dummy secrets were committed in `exposed_credentials.txt` for testing; file has been permanently removed and added to `.gitignore`, see `SECURITY_FINDINGS.md`.
