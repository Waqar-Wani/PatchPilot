import { useEffect, useMemo, useState } from "react"
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import api from "./api/client"
import "./styles.css"

const STATUS_COLORS = {
  Pending: "#9ca3af",
  Running: "#38bdf8",
  Done: "#22c55e",
  Skipped: "#f59e0b",
  Failed: "#ef4444",
}

function Navbar() {
  const links = [
    { to: "/", label: "Home" },
    { to: "/app", label: "Dashboard" },
    { to: "/how-it-works", label: "How it works" },
    { to: "/security", label: "Security Findings" },
    { to: "/stats", label: "Stats" },
  ]
  return (
    <div className="glass" style={{ display: "flex", alignItems: "center", padding: "12px 16px", gap: 14, marginBottom: 18, color: "#0a0a0a" }}>
      <div style={{ fontWeight: 800, letterSpacing: 0.4, fontSize: 16, color: "#0a0a0a" }}>PatchPilot</div>
      <div style={{ display: "flex", gap: 10, fontSize: 14 }}>
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            style={({ isActive }) => ({
              padding: "8px 12px",
              borderRadius: 10,
              textDecoration: "none",
              color: isActive ? "#0a0a0a" : "#1f2937",
              background: isActive ? "rgba(255,255,255,0.9)" : "transparent",
              border: "1px solid rgba(15,23,42,0.08)",
              boxShadow: isActive ? "0 6px 20px rgba(15,23,42,0.12)" : "none",
            })}
          >
            {l.label}
          </NavLink>
        ))}
      </div>
    </div>
  )
}

function Hero({ onSubmit, url, setUrl }) {
  return (
    <motion.div
      className="glass"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      style={{ padding: "18px", marginBottom: 16, color: "#0a0a0a" }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
        <div>
          <div className="pill">Auto-contribute · AI powered</div>
          <h1 style={{ margin: "10px 0 6px", fontSize: 24, letterSpacing: -0.2, color: "#0a0a0a" }}>Ship tiny PRs fast</h1>
          <p style={{ margin: 0, color: "#0a0a0a", fontSize: 14 }}>
            Paste any public GitHub repo. PatchPilot scans README, hunts secrets/misconfigs, and opens a PR with small, safe fixes.
          </p>
        </div>
        <div style={{ minWidth: 320, maxWidth: 420 }}>
          <div className="glass" style={{ padding: 12, borderRadius: 14 }}>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: 10,
                border: "1px solid rgba(15,23,42,0.12)",
                background: "rgba(255,255,255,0.9)",
                color: "#0a0a0a",
                fontSize: 14,
                marginBottom: 10,
              }}
            />
            <button className="btn-primary" onClick={onSubmit} style={{ width: "100%" }}>
              Contribute
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function JobsTable({ jobs, onSelect, selected, pagination, onPage }) {
  return (
    <div className="glass" style={{ padding: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <h3 style={{ margin: 0, fontSize: 16 }}>Recent jobs</h3>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Repo</th>
              <th>Type</th>
              <th>Status</th>
              <th>PR</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr
                key={j._id}
                onClick={() => onSelect(j._id)}
                style={{ cursor: "pointer", background: selected === j._id ? "rgba(255,255,255,0.04)" : "transparent" }}
              >
                <td style={{ maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {j.repo_url.replace("https://github.com/", "")}
                </td>
                <td style={{ color: "#0B1224" }}>{j.contribution_type || "—"}</td>
                <td>
                  <span className="status" style={{ color: STATUS_COLORS[(j.status || "").replace(/^[a-z]/, (c) => c.toUpperCase())] }}>
                    {(j.status || "").replace(/^[a-z]/, (c) => c.toUpperCase())}
                  </span>
                </td>
                <td>
                  {j.pr_url ? (
                    <a href={j.pr_url} target="_blank" rel="noreferrer" style={{ color: "#7dd3fc" }}>
                      View PR
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
                <td onClick={(e) => e.stopPropagation()}>
                  <button className="btn-ghost" style={{ padding: "6px 10px" }} onClick={() => onSelect(j._id, true)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 10 }}>
          <button className="btn-ghost" onClick={() => onPage(Math.max(0, pagination.skip - pagination.limit))} disabled={pagination.skip === 0}>
            Prev
          </button>
          <div style={{ color: "#94a3b8", fontSize: 13 }}>
            Showing {pagination.skip + 1}–{Math.min(pagination.skip + pagination.limit, pagination.total)} of {pagination.total}
          </div>
          <button
            className="btn-ghost"
            onClick={() => onPage(pagination.skip + pagination.limit)}
            disabled={pagination.skip + pagination.limit >= pagination.total}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

function LogsPanel({ logs, onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      className="glass"
      style={{ padding: 14 }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <strong>Logs</strong>
        <button className="btn-ghost" onClick={onClose}>
          Close
        </button>
      </div>
      <div className="log-panel">
        {logs.length === 0 ? (
          <span style={{ color: "#6b7280" }}>Waiting for logs...</span>
        ) : (
          logs.map((l, i) => (
            <div key={i}>
              <span style={{ color: "#6b7280" }}>{l.time.slice(11, 19)}</span>{" "}
              {l.msg}
            </div>
          ))
        )}
      </div>
    </motion.div>
  )
}

function Dashboard() {
  const [url, setUrl] = useState("")
  const [jobs, setJobs] = useState([])
  const [page, setPage] = useState({ skip: 0, limit: 20, total: 0 })
  const [selected, setSelected] = useState(null)
  const [logs, setLogs] = useState([])

  const fetchJobs = (skip = page.skip) =>
    api.get("/jobs", { params: { skip, limit: page.limit } }).then((r) => {
      setJobs(r.data.items)
      setPage({ skip: r.data.skip, limit: r.data.limit, total: r.data.total })
    })

  useEffect(() => {
    fetchJobs()
    const t = setInterval(() => fetchJobs(), 4000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!selected) return
    const t = setInterval(() => {
      api.get(`/jobs/${selected}`).then((r) => setLogs(r.data.logs || []))
    }, 2000)
    return () => clearInterval(t)
  }, [selected])

  const submit = async () => {
    if (!url.trim()) return
    await api.post("/contribute", { repo_url: url.trim() })
    setUrl("")
    fetchJobs()
  }

  const deleteJob = async (id) => {
    const yes = window.confirm("Delete this job?")
    if (!yes) return
    await api.delete(`/jobs/${id}`)
    if (selected === id) setSelected(null)
    fetchJobs()
  }

  return (
    <div className="grid" style={{ gap: 18 }}>
      <Hero url={url} setUrl={setUrl} onSubmit={submit} />
      <JobsTable
        jobs={jobs}
        onSelect={(id, deleteOnly = false) => (deleteOnly ? deleteJob(id) : setSelected(id))}
        selected={selected}
        pagination={page}
        onPage={(nextSkip) => fetchJobs(nextSkip)}
      />
      <AnimatePresence>{selected && <LogsPanel logs={logs} onClose={() => setSelected(null)} />}</AnimatePresence>
    </div>
  )
}

function LandingPage() {
  const [stats, setStats] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get("/stats").then((r) => setStats(r.data)).catch(() => setStats(null))
  }, [])

  const summary = stats?.summary

  return (
    <div className="grid" style={{ gap: 18 }}>
      <motion.div
        className="glass"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        style={{
          padding: 22,
          background: "linear-gradient(135deg, rgba(255, 214, 102, 0.35), rgba(124, 175, 255, 0.28))",
        }}
      >
      <div style={{ display: "flex", gap: 18, alignItems: "center", justifyContent: "space-between", color: "#0a0a0a" }}>
          <div style={{ flex: 1 }}>
            <div className="pill">PatchPilot · AI agent for tiny PRs</div>
            <h1 style={{ fontSize: 30, margin: "12px 0 8px" }}>Ship safe PRs with measurable impact</h1>
            <p style={{ color: "#0b1224", maxWidth: 560 }}>
              PatchPilot scans repos, proposes small fixes, and opens PRs with security, docs, and maintenance
              improvements. Now with live stats, costs, and credibility signals.
            </p>
            <div style={{ display: "flex", gap: 12, marginTop: 14, flexWrap: "wrap" }}>
              <button className="btn-primary" onClick={() => navigate("/app")}>Open Dashboard</button>
              <a
                className="btn-ghost"
                href="https://github.com/Waqar-Wani/PatchPilot"
                target="_blank"
                rel="noreferrer"
                style={{ display: "inline-flex", alignItems: "center", gap: 8 }}
              >
                View Repo ↗
              </a>
            </div>
          </div>
          <div style={{ flex: 1, display: "flex", justifyContent: "flex-end" }}>
            <div className="hero-visual">
              <div className="floating-orb orb-1" />
              <div className="floating-orb orb-2" />
              <div className="floating-orb orb-3" />
              <div className="mini-stats">
                <div className="mini-card">
                  <span>Completed PRs</span>
                  <strong>{summary ? summary.done : "—"}</strong>
                  <small>{summary ? `Out of ${summary.total} runs` : "Live pull requests"}</small>
                </div>
                <div className="mini-card">
                  <span>Avg cost / fix</span>
                  <strong>{summary?.avg_cost_per_fix ? `$${summary.avg_cost_per_fix.toFixed(4)}` : "—"}</strong>
                  <small>Estimated tokens</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
        {[
          { title: "Credibility", heading: "Measured performance", body: "Every run logs tokens, cost, files changed, severity, and outcome. See the stats page for live numbers." },
          { title: "Safety", heading: "Guardrails on by default", body: "Strict validation, delete restrictions, and evidence gates keep patches small and reversible." },
          { title: "Speed", heading: "Tiny PRs in minutes", body: "Focus on single, high-confidence edits: README gaps, leaked secrets, and misconfigs." },
          { title: "Trust", heading: "Transparent PRs", body: "Readable diffs, SECURITY_FINDINGS, and logs embedded in every job for quick review." },
        ].map((card, i) => (
          <motion.div
            key={card.title}
            className="glass"
            style={{ padding: 14 }}
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ delay: i * 0.08 }}
          >
            <div className="pill">{card.title}</div>
            <h3 className="card-title">{card.heading}</h3>
            <p style={{ color: "#0B1224" }}>{card.body}</p>
          </motion.div>
        ))}
      </div>

      <motion.div
        className="glass"
        style={{ padding: 18, overflow: "hidden" }}
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
      >
        <div className="pill">Architecture</div>
        <h3 className="card-title">How PatchPilot is wired</h3>
        <div className="arch-grid">
          <div>
            <h4>Backend (FastAPI + Celery)</h4>
            <ul>
              <li>FastAPI REST: `/api/contribute`, `/api/jobs`, `/api/stats`</li>
              <li>Celery worker executes git ops, applies patches, opens PRs</li>
              <li>MongoDB stores jobs, logs, metrics</li>
              <li>Redis broker for task queueing</li>
            </ul>
          </div>
          <div>
            <h4>Analysis loop</h4>
            <ul>
              <li>Repo snapshot (README, file tree, sensitive hints)</li>
              <li>LLM via OpenRouter with guardrails + verification</li>
              <li>Safety gates: evidence check, delete whitelist, non-empty content</li>
            </ul>
          </div>
          <div>
            <h4>Git + PR flow</h4>
            <ul>
              <li>Clone (fork if no push rights)</li>
              <li>Apply scoped changes, commit with defaults</li>
              <li>Push branch and open PR with summary</li>
            </ul>
          </div>
          <div>
            <h4>Metrics & trust</h4>
            <ul>
              <li>Tokens, cost, files/lines changed, severity per run</li>
              <li>Success/skip/fail counts and cost per fix</li>
              <li>Visible in UI stats page and `/api/stats` JSON</li>
            </ul>
          </div>
        </div>
      </motion.div>

      <motion.div
        className="glass"
        style={{ padding: 18 }}
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
      >
        <div className="pill">Visual DFD</div>
        <p style={{ marginTop: 8, color: "#0b1224" }}>
        </p>
        <div className="dfd-frame">
          <img src="/dfd.png" alt="PatchPilot data flow diagram" className="dfd-img" onError={(e)=>{e.target.style.display='none';}} />
          <div className="dfd-placeholder">
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function HowItWorks() {
  const steps = useMemo(
    () => [
      { title: "Scan & snapshot", body: "We fetch README, key files, open issues, and build a concise snapshot.", emoji: "📥" },
      { title: "Analyze", body: "LLM selects a small, safe improvement: docs, tests, or security notes.", emoji: "🧠" },
      { title: "Guardrails", body: "Evidence gate, delete whitelist, empty-content checks, branch defaults.", emoji: "🛡️" },
      { title: "Patch & PR", body: "We branch (or fork), apply the patch, push, and open a PR with friendly context.", emoji: "🚀" },
      { title: "Measure", body: "Tokens, cost, files/lines changed, severity, PR link are logged to stats.", emoji: "📊" },
    ],
    []
  )
  return (
    <motion.div className="glass" style={{ padding: 18 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <h2 style={{ marginTop: 0 }}>How it works</h2>
      <div className="hero-grid">
        {steps.map((s, i) => (
          <motion.div
            key={i}
            className="glass"
            style={{ padding: 16, position: "relative", overflow: "hidden" }}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
          >
            <div className="floating-emoji">{s.emoji}</div>
            <div className="pill">Step {i + 1}</div>
            <h3 className="card-title">{s.title}</h3>
            <p style={{ color: "#0a0a0a", margin: 0 }}>{s.body}</p>
          </motion.div>
        ))}
      </div>
      <p style={{ color: "#0a0a0a", marginTop: 12 }}>
        Want proof? Run a repo, then open the Stats page: success/skip/fail counts, cost, tokens, severity, and PR links are recorded.
      </p>
    </motion.div>
  )
}

function SecurityPage() {
  return (
    <motion.div className="glass" style={{ padding: 18 }} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <h2 style={{ marginTop: 0 }}>Security findings</h2>
      <div className="security-grid">
        <div className="glass sec-card">
          <div className="pill">Secret hunting</div>
          <h3 className="card-title">Automatic leak detection</h3>
          <p>We scan filenames (.env, key, token, credential, pem) and contents; flagged files trigger remediation.</p>
        </div>
        <div className="glass sec-card">
          <div className="pill">Safe remediation</div>
          <h3 className="card-title">No raw secrets in PR</h3>
          <p>Secrets are deleted/ignored and documented in SECURITY_FINDINGS.md. We never echo secret values.</p>
        </div>
        <div className="glass sec-card">
          <div className="pill">Guardrails</div>
          <h3 className="card-title">Delete whitelist</h3>
          <p>Only detected secret files can be removed; all other deletes are blocked. Edits require non-empty content.</p>
        </div>
        <div className="glass sec-card">
          <div className="pill">Signals</div>
          <h3 className="card-title">Severity & metrics</h3>
          <p>Security fixes are marked critical, with token/cost metrics and PR links surfaced in Stats.</p>
        </div>
      </div>
      <div className="sec-cta">
        <div>
          <h4 style={{ margin: "0 0 6px" }}>Try a security run</h4>
          <p style={{ margin: 0 }}>Paste a repo with a test secret file (e.g., exposed_credentials.txt) and watch the PR.</p>
        </div>
        <div className="shield">🛡️</div>
      </div>
    </motion.div>
  )
}

function StatCard({ title, value, sub }) {
  return (
    <div className="glass" style={{ padding: 14 }}>
      <div style={{ fontSize: 12, color: "#9fb3ff", textTransform: "uppercase", letterSpacing: 0.8 }}>{title}</div>
      <div style={{ fontSize: 22, fontWeight: 800, marginTop: 4 }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function StatsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState({ skip: 0, limit: 50, total: 0 })

  const fetchStats = async (skip = page.skip) => {
    try {
      const r = await api.get("/stats", { params: { skip, limit: page.limit } })
      setData(r.data)
      setPage({ skip: r.data.skip, limit: r.data.limit, total: r.data.total })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  if (loading) return <div className="glass" style={{ padding: 18 }}>Loading stats…</div>
  if (!data) return <div className="glass" style={{ padding: 18 }}>No stats yet.</div>

  const { summary, runs } = data

  return (
    <div className="grid" style={{ gap: 14 }}>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
        <StatCard title="Total runs" value={summary.total} sub="All jobs" />
        <StatCard title="Completed" value={summary.done} sub="status: Done" />
        <StatCard title="Skipped" value={summary.skipped} sub="No action taken" />
        <StatCard title="Failed" value={summary.failed} sub="Errors" />
        <StatCard title="Total cost" value={`$${(summary.total_cost_usd || 0).toFixed(4)}`} sub="Estimated" />
        <StatCard
          title="Avg cost per fix"
          value={summary.avg_cost_per_fix ? `$${summary.avg_cost_per_fix.toFixed(4)}` : "—"}
          sub="Done runs only"
        />
      </div>

      <div className="glass" style={{ padding: 14 }}>
        <h3 style={{ marginTop: 0, marginBottom: 8 }}>Runs</h3>
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Repo</th>
                <th>Status</th>
                <th>Severity</th>
                <th>Files</th>
                <th>Lines</th>
                <th>PR</th>
                <th>Tokens</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r, i) => (
                <tr key={i}>
                  <td style={{ maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {r.repo}
                  </td>
                  <td style={{ color: STATUS_COLORS[(r.status || "").replace(/^[a-z]/, (c) => c.toUpperCase())] || "#e5e7eb" }}>
                    {(r.status || "").replace(/^[a-z]/, (c) => c.toUpperCase())}
                  </td>
                  <td>{r.severity || "—"}</td>
                  <td>
                    {r.files
                      ? `${r.files.edited || 0}e/${r.files.created || 0}c/${r.files.deleted || 0}d`
                      : "—"}
                  </td>
                  <td>
                    {r.changes
                      ? `+${r.changes.lines_added || 0}/-${r.changes.lines_removed || 0}`
                      : "—"}
                  </td>
                  <td>
                    {r.pr_url ? (
                      <a href={r.pr_url} target="_blank" rel="noreferrer" style={{ color: "#7dd3fc" }}>
                        PR
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{r.tokens_used ?? "—"}</td>
                  <td>{r.cost_usd != null ? `$${r.cost_usd.toFixed(4)}` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginTop: 10 }}>
          <button className="btn-ghost" onClick={() => fetchStats(Math.max(0, page.skip - page.limit))} disabled={page.skip === 0}>
            Prev
          </button>
          <div style={{ color: "#94a3b8", fontSize: 13 }}>
            Showing {page.skip + 1}–{Math.min(page.skip + page.limit, page.total)} of {page.total}
          </div>
          <button
            className="btn-ghost"
            onClick={() => fetchStats(page.skip + page.limit)}
            disabled={page.skip + page.limit >= page.total}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Navbar />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app" element={<Dashboard />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="/security" element={<SecurityPage />} />
          <Route path="/stats" element={<StatsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
