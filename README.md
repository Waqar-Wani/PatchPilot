# PatchPilot 🚀🛠️

PatchPilot is a full-stack dashboard that lets you paste any public GitHub repo and have an AI make a safe, small contribution, open a PR, and show live progress. It also checks for README gaps and possible secret leaks, dropping findings into `SECURITY_FINDINGS.md`. (Yes, even the mysterious **dfds** use‑case is covered. 😉)

## Features ✨
- 📡 Paste a repo URL and kick off an AI-driven contribution job.
- 🧠 Snapshot + analysis to propose docs/tests or security findings.
- 🔀 Auto-branch, patch, push, and open a PR (GitHub API).
- 📺 Live job/status/logs in a modern React UI with animations.
- 🧹 Delete completed jobs from the UI.
- 🔒 Secret/misconfig detection summary in `SECURITY_FINDINGS.md`.

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

## Quickstart Example
```bash
# Clone the repo
git clone https://github.com/Waqar-Wani/PatchPilot
cd PatchPilot

# Set up environment variables
cp .env.example .env
# Fill in the required values in .env

# Start the backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# Start the worker
celery -A celery_app worker --loglevel=info --pool=solo

# Start the frontend
cd ../frontend
npm install
npm run dev

# Open the UI at http://127.0.0.1:5174 and paste a repo URL to start a contribution job.
```

## Known issues for testing
- Security: dummy secrets committed in `exposed_credentials.txt` to verify leak detection.
