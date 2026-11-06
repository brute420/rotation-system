import { useState, useEffect, useCallback } from "react"

const API = "http://localhost:8000/api"

const SKILL_COLORS = {
  Inspection:   { bg: "#0f3460", accent: "#e94560", light: "#1a4a7a" },
  Fumigation:   { bg: "#1b4332", accent: "#52b788", light: "#2d6a4f" },
  Sampling:     { bg: "#3d2b1f", accent: "#e07a5f", light: "#5c3d2e" },
  Clearance:    { bg: "#1a1a2e", accent: "#a78bfa", light: "#2d2d4e" },
  Verification: { bg: "#1f2937", accent: "#fbbf24", light: "#374151" },
}
const SKILL_ICONS = {
  Inspection: "🔍", Fumigation: "🌿", Sampling: "🧪",
  Clearance: "✅", Verification: "🛡",
}
const STATUS_COLORS = {
  draft:    { bg: "#1e293b", text: "#94a3b8", dot: "#475569" },
  pending:  { bg: "#1c1917", text: "#fbbf24", dot: "#f59e0b" },
  approved: { bg: "#052e16", text: "#4ade80", dot: "#22c55e" },
  rejected: { bg: "#450a0a", text: "#f87171", dot: "#ef4444" },
}

function Badge({ text, color = "#60a5fa", bg = "rgba(96,165,250,0.12)" }) {
  return (
    <span style={{ background: bg, color, padding: "2px 8px", borderRadius: "5px",
      fontSize: "10px", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase" }}>
      {text}
    </span>
  )
}

function StatusPill({ status }) {
  const c = STATUS_COLORS[status] || STATUS_COLORS.draft
  return (
    <span style={{ background: c.bg, color: c.text, padding: "3px 10px", borderRadius: "20px",
      fontSize: "11px", fontWeight: 600, display: "inline-flex", alignItems: "center", gap: "5px" }}>
      <span style={{ width: "6px", height: "6px", borderRadius: "50%",
        background: c.dot, display: "inline-block" }} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function StatCard({ label, value, icon, color }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: "12px", padding: "18px 22px", flex: 1, minWidth: "120px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ fontSize: "26px", fontWeight: 700, color: color || "#fff",
          fontFamily: "monospace", letterSpacing: "-1px" }}>{value ?? "—"}</div>
        <span style={{ fontSize: "18px", opacity: 0.5 }}>{icon}</span>
      </div>
      <div style={{ fontSize: "11px", color: "#9ca3af", marginTop: "4px",
        textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</div>
    </div>
  )
}

function AssignmentCard({ item, index }) {
  const c = SKILL_COLORS[item.skill] || SKILL_COLORS.Inspection
  return (
    <div style={{ background: `linear-gradient(135deg,${c.bg} 0%,${c.light} 100%)`,
      border: `1px solid ${c.accent}33`, borderLeft: `3px solid ${c.accent}`,
      borderRadius: "10px", padding: "14px 18px", display: "flex",
      alignItems: "center", gap: "14px",
      animation: `slideIn 0.3s ease ${index * 0.04}s both` }}>
      <span style={{ fontSize: "20px" }}>{SKILL_ICONS[item.skill] || "📋"}</span>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "14px", fontWeight: 600, color: "#fff" }}>{item.officer}</span>
          {item.role === "Supervisor" && (
            <Badge text="Supervisor" color="#fbbf24" bg="rgba(251,191,36,0.15)" />
          )}
        </div>
        <div style={{ fontSize: "11px", color: "#9ca3af", marginTop: "2px" }}>
          {item.badge} · {item.skill}
        </div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontSize: "13px", color: c.accent, fontWeight: 500 }}>{item.shed}</div>
        <div style={{ fontSize: "10px", color: "#6b7280", marginTop: "3px" }}>
          {item.start_date} → {item.end_date}
        </div>
        <div style={{ fontSize: "10px", color: "#4b5563" }}>WL: {item.workload}</div>
      </div>
    </div>
  )
}

function UnassignedCard({ item }) {
  return (
    <div style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
      borderRadius: "10px", padding: "12px 16px", display: "flex", gap: "10px" }}>
      <span style={{ fontSize: "18px" }}>⚠️</span>
      <div>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "#fca5a5" }}>{item.shed}</div>
        <div style={{ fontSize: "11px", color: "#9ca3af", marginTop: "3px" }}>
          Needs: {item.required_skill} · Priority {item.priority}
        </div>
        <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>{item.reason}</div>
      </div>
    </div>
  )
}

function Inp({ label, type = "text", value, onChange, placeholder }) {
  return (
    <div style={{ marginBottom: "12px" }}>
      {label && <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px",
        textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>}
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{ width: "100%", background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px",
          padding: "9px 12px", color: "#fff", fontSize: "13px",
          outline: "none", fontFamily: "inherit" }} />
    </div>
  )
}

function Sel({ label, value, onChange, options }) {
  return (
    <div style={{ marginBottom: "12px" }}>
      {label && <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px",
        textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>}
      <select value={value} onChange={e => onChange(e.target.value)}
        style={{ width: "100%", background: "#1e293b",
          border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px",
          padding: "9px 12px", color: "#fff", fontSize: "13px",
          outline: "none", fontFamily: "inherit" }}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function Btn({ children, onClick, disabled, variant = "primary", size = "md" }) {
  const v = {
    primary: { background: "linear-gradient(135deg,#e94560,#c0392b)", color: "#fff", border: "none" },
    success: { background: "linear-gradient(135deg,#16a34a,#15803d)", color: "#fff", border: "none" },
    danger:  { background: "rgba(239,68,68,0.15)", color: "#f87171", border: "1px solid rgba(239,68,68,0.3)" },
    ghost:   { background: "rgba(255,255,255,0.05)", color: "#9ca3af", border: "1px solid rgba(255,255,255,0.1)" },
    warning: { background: "rgba(251,191,36,0.15)", color: "#fbbf24", border: "1px solid rgba(251,191,36,0.3)" },
  }[variant] || {}
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ ...v, padding: size === "sm" ? "6px 12px" : "10px 20px",
        borderRadius: "8px", fontWeight: 600,
        fontSize: size === "sm" ? "12px" : "13px",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1, fontFamily: "inherit" }}>
      {children}
    </button>
  )
}

function SectionHead({ title }) {
  return (
    <div style={{ fontSize: "10px", color: "#4b5563", textTransform: "uppercase",
      letterSpacing: "0.12em", fontWeight: 700, marginBottom: "12px",
      paddingBottom: "8px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
      {title}
    </div>
  )
}

function FormCard({ children }) {
  return (
    <div style={{ background: "rgba(255,255,255,0.03)",
      border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", padding: "20px" }}>
      {children}
    </div>
  )
}

export default function App() {
  const [tab, setTab]             = useState("rotate")
  const [loading, setLoading]     = useState(false)
  const [resetting, setResetting] = useState(false)
  const [result, setResult]       = useState(null)
  const [stats, setStats]         = useState(null)
  const [officers, setOfficers]   = useState([])
  const [sheds, setSheds]         = useState([])
  const [runs, setRuns]           = useState([])
  const [leaves, setLeaves]       = useState([])
  const [swaps, setSwaps]         = useState([])
  const [error, setError]         = useState(null)
  const [toast, setToast]         = useState(null)
  const [weekStart, setWeekStart] = useState(new Date().toISOString().split("T")[0])

  const [lvOfficer, setLvOfficer] = useState("")
  const [lvStart,   setLvStart]   = useState("")
  const [lvEnd,     setLvEnd]     = useState("")
  const [lvReason,  setLvReason]  = useState("")

  const [swReq,     setSwReq]     = useState("")
  const [swTgt,     setSwTgt]     = useState("")
  const [swReqShed, setSwReqShed] = useState("")
  const [swTgtShed, setSwTgtShed] = useState("")
  const [swReason,  setSwReason]  = useState("")

  const showToast = (msg, type = "success") => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  const apiFetch = useCallback(async (url, opts = {}) => {
    const r = await fetch(`${API}${url}`, opts)
    return r.json()
  }, [])

  const fetchAll = useCallback(async () => {
    try {
      const [s, o, sh, r, l, sw] = await Promise.all([
        apiFetch("/stats/"), apiFetch("/officers/"), apiFetch("/sheds/"),
        apiFetch("/runs/"), apiFetch("/leave/list/"), apiFetch("/swap/list/"),
      ])
      if (s.status  === "success") setStats(s)
      if (o.status  === "success") setOfficers(o.officers)
      if (sh.status === "success") setSheds(sh.sheds)
      if (r.status  === "success") setRuns(r.runs)
      if (l.status  === "success") setLeaves(l.leaves)
      if (sw.status === "success") setSwaps(sw.swaps)
    } catch {}
  }, [apiFetch])

  useEffect(() => { fetchAll() }, [fetchAll])

  const post = (url, body) => apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  const handleRotate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const d = await post("/rotate/", { week_start: weekStart })
      if (d.status === "success") {
        setResult(d)
        // ── Fixed: handle all edge cases properly ──
        if (d.total_assigned === 0 && d.total_unassigned === 0) {
          setError("No sheds found. Check your database.")
        } else if (d.total_assigned === 0) {
          setError("All officers have completed this rotation cycle. Click Reset Cycle first, then Generate again.")
        } else if (d.total_unassigned > 0) {
          showToast(`✓ ${d.total_assigned} assigned, ${d.total_unassigned} unassigned (check reasons below)`, "info")
        } else {
          showToast(`✓ ${d.total_assigned} assigned — pending OIC approval`, "info")
        }
        fetchAll()
      } else {
        setError(d.message || "Server returned an error. Check the backend window.")
      }
    } catch {
      setError("Cannot connect to backend. Make sure the backend CMD window is open and running.")
    }
    setLoading(false)
  }

  const handleReset = async () => {
    if (!confirm("Reset ALL rotation history and workload points? This cannot be undone.")) return
    setResetting(true)
    setResult(null)
    setError(null)
    try {
      const d = await post("/rotate/reset/", {})
      if (d.status === "success") {
        showToast("↺ Rotation cycle reset. You can now generate a fresh roster.")
        fetchAll()
      } else {
        showToast("Reset failed: " + (d.message || "unknown error"), "error")
      }
    } catch {
      showToast("Cannot connect to backend", "error")
    }
    setResetting(false)
  }

  const handleApproveRun = async (runId) => {
    const approver = prompt("Enter approver name (Officer in Charge):") || "Officer in Charge"
    const d = await post(`/runs/${runId}/approve/`, { approved_by: approver })
    if (d.status === "success") { showToast(`✓ Run #${runId} approved by ${approver}`); fetchAll() }
    else showToast(d.message || "Approval failed", "error")
  }

  const handleRejectRun = async (runId) => {
    const reason = prompt("Enter reason for rejection:")
    if (!reason) return
    const who = prompt("Enter your name:") || "Officer in Charge"
    const d = await post(`/runs/${runId}/reject/`, { reason, rejected_by: who })
    if (d.status === "success") { showToast(`Run #${runId} rejected`, "error"); fetchAll() }
  }

  const handleSubmitLeave = async () => {
    if (!lvOfficer || !lvStart || !lvEnd) {
      showToast("Please fill in officer, start date and end date", "error"); return
    }
    const d = await post("/leave/", {
      officer_id: parseInt(lvOfficer), start_date: lvStart,
      end_date: lvEnd, reason: lvReason,
    })
    if (d.status === "success") {
      showToast("Leave request submitted successfully")
      setLvOfficer(""); setLvStart(""); setLvEnd(""); setLvReason("")
      fetchAll()
    } else showToast(d.message || "Failed to submit leave", "error")
  }

  const handleActionLeave = async (id, action) => {
    const who = prompt("Enter your name:") || "Officer in Charge"
    const d = await post(`/leave/${id}/action/`, { action, approved_by: who })
    if (d.status === "success") { showToast(d.message); fetchAll() }
    else showToast(d.message || "Action failed", "error")
  }

  const handleSubmitSwap = async () => {
    if (!swReq || !swTgt || !swReqShed || !swTgtShed) {
      showToast("Please fill in all swap fields", "error"); return
    }
    const d = await post("/swap/", {
      requester_id: parseInt(swReq), target_officer_id: parseInt(swTgt),
      requester_shed_id: parseInt(swReqShed), target_shed_id: parseInt(swTgtShed),
      reason: swReason,
    })
    if (d.status === "success") {
      showToast("Swap request submitted successfully")
      setSwReq(""); setSwTgt(""); setSwReqShed(""); setSwTgtShed(""); setSwReason("")
      fetchAll()
    } else showToast(d.message || "Failed to submit swap", "error")
  }

  const handleActionSwap = async (id, action) => {
    const who = prompt("Enter your name:") || "Officer in Charge"
    const d = await post(`/swap/${id}/action/`, { action, approved_by: who })
    if (d.status === "success") { showToast(d.message); fetchAll() }
    else showToast(d.message || "Action failed", "error")
  }

  const tabs = [
    { id: "rotate",   label: "⚡ Rotate"   },
    { id: "approve",  label: "✅ Approvals" },
    { id: "leave",    label: "📅 Leave"     },
    { id: "swap",     label: "🔄 Swaps"     },
    { id: "officers", label: "👥 Officers"  },
    { id: "workload", label: "📊 Workload"  },
  ]

  return (
    <div style={{ minHeight: "100vh", background: "#080c14", color: "#e2e8f0",
      fontFamily: "'Segoe UI', Arial, sans-serif" }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        button { cursor: pointer; border: none; outline: none; font-family: inherit; }
        input, select { outline: none; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }
        @keyframes toastIn {
          from { opacity: 0; transform: translateX(30px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>

      {/* Toast */}
      {toast && (
        <div style={{ position: "fixed", top: "18px", right: "18px", zIndex: 999,
          background: toast.type === "error" ? "#450a0a" : toast.type === "info" ? "#0c1a3d" : "#052e16",
          border: `1px solid ${toast.type === "error" ? "#7f1d1d" : toast.type === "info" ? "#1e3a8a" : "#14532d"}`,
          borderRadius: "10px", padding: "12px 16px", fontSize: "13px",
          color: "#fff", animation: "toastIn 0.25s ease", maxWidth: "340px",
          lineHeight: "1.5" }}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={{ background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.05)",
        padding: "0 20px", position: "sticky", top: 0, zIndex: 100, backdropFilter: "blur(10px)" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto", display: "flex",
          alignItems: "center", justifyContent: "space-between", height: "60px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "34px", height: "34px", borderRadius: "8px",
              background: "linear-gradient(135deg,#e94560,#0f3460)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: "16px" }}>🛂</div>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 700 }}>KEBS JKIA</div>
              <div style={{ fontSize: "9px", color: "#475569", textTransform: "uppercase",
                letterSpacing: "0.12em" }}>Officer Rotation System</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: "2px", background: "rgba(255,255,255,0.03)",
            borderRadius: "10px", padding: "3px" }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} style={{
                padding: "6px 11px", borderRadius: "7px", fontSize: "11px", fontWeight: 500,
                background: tab === t.id ? "rgba(255,255,255,0.09)" : "transparent",
                color: tab === t.id ? "#fff" : "#4b5563", position: "relative" }}>
                {t.label}
                {t.id === "approve" && stats?.pending_approvals > 0 && (
                  <span style={{ position: "absolute", top: "2px", right: "3px",
                    background: "#e94560", color: "#fff", borderRadius: "50%",
                    width: "14px", height: "14px", fontSize: "9px", fontWeight: 700,
                    display: "flex", alignItems: "center", justifyContent: "center" }}>
                    {stats.pending_approvals}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "24px 20px" }}>

        {/* Stats */}
        {stats && (
          <div style={{ display: "flex", gap: "10px", marginBottom: "24px", flexWrap: "wrap" }}>
            <StatCard label="Officers"      value={stats.total_officers}        color="#60a5fa" icon="👥" />
            <StatCard label="Sheds"         value={stats.total_sheds}           color="#a78bfa" icon="🏗" />
            <StatCard label="Completed"     value={stats.completed_assignments} color="#34d399" icon="✓"  />
            <StatCard label="Pending"       value={stats.pending_assignments}   color="#fbbf24" icon="⏳" />
            <StatCard label="Need Approval" value={stats.pending_approvals}     color="#f87171" icon="⚠"  />
            <StatCard label="On Leave"      value={stats.officers_on_leave}     color="#fb923c" icon="📅" />
          </div>
        )}

        {/* ── ROTATE ── */}
        {tab === "rotate" && (
          <div>
            <div style={{ display: "flex", gap: "10px", marginBottom: "16px",
              alignItems: "flex-end", flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: "10px", color: "#9ca3af", marginBottom: "4px",
                  textTransform: "uppercase", letterSpacing: "0.06em" }}>Assignment Start Date</div>
                <input type="date" value={weekStart} onChange={e => setWeekStart(e.target.value)}
                  style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px", padding: "9px 12px", color: "#fff",
                    fontSize: "13px", outline: "none", fontFamily: "inherit" }} />
              </div>
              <Btn onClick={handleRotate} disabled={loading}>
                {loading ? "⏳ Running CSP Algorithm..." : "⚡ Generate Roster"}
              </Btn>
              <Btn onClick={handleReset} disabled={resetting} variant="ghost">
                {resetting ? "Resetting..." : "↺ Reset Cycle"}
              </Btn>
            </div>

            {/* Info banner */}
            <div style={{ padding: "10px 14px", background: "rgba(251,191,36,0.07)",
              border: "1px solid rgba(251,191,36,0.2)", borderRadius: "8px",
              fontSize: "12px", color: "#fbbf24", marginBottom: "16px" }}>
              ℹ  Rosters require OIC approval before going live.
              Each assignment covers a <strong>2-week period</strong>.
              If all officers have been assigned, click <strong>Reset Cycle</strong> first.
            </div>

            {/* Error */}
            {error && (
              <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
                borderRadius: "10px", padding: "14px 18px", fontSize: "13px",
                color: "#fca5a5", marginBottom: "18px", lineHeight: "1.6" }}>
                ⚠️ {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <div>
                {/* Run summary bar */}
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center",
                  marginBottom: "16px", background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px",
                  padding: "12px 16px", fontSize: "12px" }}>
                  <span style={{ color: "#6b7280" }}>Run #{result.run_id}</span>
                  <span style={{ color: "#374151" }}>·</span>
                  <span style={{ color: "#9ca3af" }}>
                    {result.week_start} → {result.week_end}
                  </span>
                  <span style={{ color: "#374151" }}>·</span>
                  <span style={{ color: "#34d399" }}>✓ {result.total_assigned} assigned</span>
                  {result.total_unassigned > 0 && (
                    <>
                      <span style={{ color: "#374151" }}>·</span>
                      <span style={{ color: "#f87171" }}>⚠ {result.total_unassigned} unassigned</span>
                    </>
                  )}
                  <StatusPill status={result.run_status} />
                </div>

                {result.assignments && result.assignments.length > 0 && (
                  <div>
                    <SectionHead title={`Assignments (${result.assignments.length})`} />
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {result.assignments.map((item, i) => (
                        <AssignmentCard key={i} item={item} index={i} />
                      ))}
                    </div>
                  </div>
                )}

                {result.unassigned && result.unassigned.length > 0 && (
                  <div style={{ marginTop: "20px" }}>
                    <SectionHead title={`Unassigned Sheds (${result.unassigned.length})`} />
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {result.unassigned.map((item, i) => (
                        <UnassignedCard key={i} item={item} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── APPROVALS ── */}
        {tab === "approve" && (
          <div>
            <SectionHead title={`Rotation Runs — ${runs.length} total`} />
            {runs.length === 0 && (
              <p style={{ color: "#4b5563", fontSize: "13px", padding: "20px 0" }}>
                No runs yet. Go to the Rotate tab and click Generate Roster.
              </p>
            )}
            {runs.map(run => (
              <div key={run.id} style={{ background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px",
                padding: "16px 20px", marginBottom: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between",
                  alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                      <span style={{ fontSize: "14px", fontWeight: 600 }}>Run #{run.id}</span>
                      <StatusPill status={run.status} />
                    </div>
                    <div style={{ fontSize: "12px", color: "#6b7280" }}>
                      {run.run_at} · Period: {run.week_start || "—"}
                    </div>
                    <div style={{ fontSize: "12px", color: "#9ca3af", marginTop: "2px" }}>
                      {run.total_assigned} assigned · {run.total_unassigned} unassigned
                      {run.approved_by && ` · ${run.status === "approved" ? "Approved" : "Actioned"} by: ${run.approved_by}`}
                    </div>
                  </div>
                  {run.status === "pending" && (
                    <div style={{ display: "flex", gap: "8px" }}>
                      <Btn onClick={() => handleApproveRun(run.id)} variant="success" size="sm">
                        ✓ Approve
                      </Btn>
                      <Btn onClick={() => handleRejectRun(run.id)} variant="danger" size="sm">
                        ✗ Reject
                      </Btn>
                    </div>
                  )}
                </div>
                {run.assignments && run.assignments.length > 0 && (
                  <div style={{ marginTop: "12px", borderTop: "1px solid rgba(255,255,255,0.05)",
                    paddingTop: "10px" }}>
                    <div style={{ fontSize: "10px", color: "#4b5563", textTransform: "uppercase",
                      letterSpacing: "0.1em", marginBottom: "8px" }}>Assignments Preview</div>
                    {run.assignments.slice(0, 5).map((a, i) => (
                      <div key={i} style={{ display: "flex", gap: "8px", fontSize: "12px",
                        color: "#9ca3af", alignItems: "center", marginBottom: "4px" }}>
                        <span style={{ color: SKILL_COLORS[a.skill]?.accent || "#fff" }}>
                          {SKILL_ICONS[a.skill]}
                        </span>
                        <span style={{ color: "#d1d5db", fontWeight: 500 }}>{a.officer}</span>
                        {a.role === "Supervisor" && (
                          <Badge text="SUP" color="#fbbf24" bg="rgba(251,191,36,0.1)" />
                        )}
                        <span>→ {a.shed}</span>
                        <span style={{ color: "#4b5563" }}>({a.start_date} to {a.end_date})</span>
                      </div>
                    ))}
                    {run.assignments.length > 5 && (
                      <div style={{ fontSize: "11px", color: "#4b5563", marginTop: "4px" }}>
                        + {run.assignments.length - 5} more assignments...
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── LEAVE ── */}
        {tab === "leave" && (
          <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "24px" }}>
            <div>
              <SectionHead title="Submit Leave Request" />
              <FormCard>
                <Sel label="Officer" value={lvOfficer} onChange={setLvOfficer}
                  options={[{ value: "", label: "Select officer..." },
                    ...officers.map(o => ({ value: o.id, label: `${o.name} (${o.skill})` }))]} />
                <Inp label="Start Date" type="date" value={lvStart} onChange={setLvStart} />
                <Inp label="End Date"   type="date" value={lvEnd}   onChange={setLvEnd} />
                <Inp label="Reason (optional)" value={lvReason} onChange={setLvReason}
                  placeholder="Annual leave, medical..." />
                <Btn onClick={handleSubmitLeave}>Submit Request</Btn>
              </FormCard>
            </div>
            <div>
              <SectionHead title={`Leave Records — ${leaves.length}`} />
              {leaves.length === 0 && (
                <p style={{ color: "#4b5563", fontSize: "13px" }}>No leave requests yet.</p>
              )}
              {leaves.map(l => (
                <div key={l.id} style={{ background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px",
                  padding: "14px 16px", marginBottom: "8px", display: "flex",
                  justifyContent: "space-between", alignItems: "center",
                  flexWrap: "wrap", gap: "10px" }}>
                  <div>
                    <div style={{ fontSize: "13px", fontWeight: 600 }}>{l.officer}</div>
                    <div style={{ fontSize: "11px", color: "#9ca3af", marginTop: "3px" }}>
                      {l.start_date} → {l.end_date}
                    </div>
                    {l.reason && (
                      <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>
                        {l.reason}
                      </div>
                    )}
                  </div>
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <StatusPill status={l.status} />
                    {l.status === "pending" && (
                      <>
                        <Btn onClick={() => handleActionLeave(l.id, "approve")} variant="success" size="sm">✓</Btn>
                        <Btn onClick={() => handleActionLeave(l.id, "reject")}  variant="danger"  size="sm">✗</Btn>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SWAPS ── */}
        {tab === "swap" && (
          <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "24px" }}>
            <div>
              <SectionHead title="Request Shed Swap" />
              <FormCard>
                <Sel label="Officer Requesting Swap" value={swReq} onChange={setSwReq}
                  options={[{ value: "", label: "Select officer..." },
                    ...officers.map(o => ({ value: o.id, label: o.name }))]} />
                <Sel label="Their Current Shed" value={swReqShed} onChange={setSwReqShed}
                  options={[{ value: "", label: "Select shed..." },
                    ...sheds.map(s => ({ value: s.id, label: s.name }))]} />
                <Sel label="Swap With Officer" value={swTgt} onChange={setSwTgt}
                  options={[{ value: "", label: "Select officer..." },
                    ...officers.map(o => ({ value: o.id, label: o.name }))]} />
                <Sel label="Their Current Shed" value={swTgtShed} onChange={setSwTgtShed}
                  options={[{ value: "", label: "Select shed..." },
                    ...sheds.map(s => ({ value: s.id, label: s.name }))]} />
                <Inp label="Reason (optional)" value={swReason} onChange={setSwReason}
                  placeholder="Reason for swap..." />
                <Btn onClick={handleSubmitSwap}>🔄 Submit Swap Request</Btn>
              </FormCard>
            </div>
            <div>
              <SectionHead title={`Swap Requests — ${swaps.length}`} />
              {swaps.length === 0 && (
                <p style={{ color: "#4b5563", fontSize: "13px" }}>No swap requests yet.</p>
              )}
              {swaps.map(s => (
                <div key={s.id} style={{ background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px",
                  padding: "14px 16px", marginBottom: "8px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between",
                    alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "6px" }}>
                        {s.requester} ↔ {s.target_officer}
                      </div>
                      <div style={{ fontSize: "11px", color: "#9ca3af" }}>
                        <span style={{ color: "#60a5fa" }}>{s.requester_shed}</span>
                        <span style={{ color: "#4b5563" }}> ↔ </span>
                        <span style={{ color: "#a78bfa" }}>{s.target_shed}</span>
                      </div>
                      {s.reason && (
                        <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "4px" }}>
                          {s.reason}
                        </div>
                      )}
                      <div style={{ fontSize: "10px", color: "#374151", marginTop: "4px" }}>
                        {s.created_at}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <StatusPill status={s.status} />
                      {s.status === "pending" && (
                        <>
                          <Btn onClick={() => handleActionSwap(s.id, "approve")} variant="success" size="sm">✓ Approve</Btn>
                          <Btn onClick={() => handleActionSwap(s.id, "reject")}  variant="danger"  size="sm">✗ Reject</Btn>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── OFFICERS ── */}
        {tab === "officers" && (
          <div>
            <SectionHead title={`${officers.length} Active Officers`} />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(260px,1fr))", gap: "10px" }}>
              {officers.map(o => {
                const c = SKILL_COLORS[o.skill] || SKILL_COLORS.Inspection
                return (
                  <div key={o.id} style={{
                    background: `linear-gradient(135deg,${c.bg}cc 0%,#080c14 100%)`,
                    border: `1px solid ${c.accent}22`, borderRadius: "10px", padding: "16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between",
                      alignItems: "flex-start" }}>
                      <div>
                        <div style={{ fontSize: "14px", fontWeight: 600 }}>{o.name}</div>
                        <div style={{ fontSize: "10px", color: "#6b7280",
                          fontFamily: "monospace", marginTop: "2px" }}>{o.badge_number}</div>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column",
                        gap: "4px", alignItems: "flex-end" }}>
                        <Badge text={o.skill} color={c.accent} bg={`${c.accent}18`} />
                        {o.role === "Supervisor" && (
                          <Badge text="Supervisor" color="#fbbf24" bg="rgba(251,191,36,0.12)" />
                        )}
                      </div>
                    </div>
                    <div style={{ marginTop: "12px", display: "flex",
                      alignItems: "center", gap: "8px" }}>
                      <div style={{ flex: 1, background: "rgba(255,255,255,0.06)",
                        borderRadius: "4px", height: "4px" }}>
                        <div style={{ width: `${Math.min(o.workload_points * 10, 100)}%`,
                          height: "100%", background: c.accent, borderRadius: "4px" }} />
                      </div>
                      <span style={{ fontSize: "10px", color: "#6b7280",
                        fontFamily: "monospace" }}>{o.workload_points} pts</span>
                    </div>
                    {o.email && (
                      <div style={{ fontSize: "10px", color: "#374151", marginTop: "8px" }}>
                        {o.email}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ── WORKLOAD ── */}
        {tab === "workload" && stats && (
          <div>
            <SectionHead title="Workload Distribution" />
            <div style={{ background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: "12px", padding: "20px 24px", marginBottom: "24px" }}>
              {stats.workload_distribution.length === 0 && (
                <p style={{ color: "#4b5563", fontSize: "13px" }}>
                  No workload data yet. Generate a roster first.
                </p>
              )}
              {stats.workload_distribution.map((o, i) => {
                const c = SKILL_COLORS[o.skill] || SKILL_COLORS.Inspection
                const pct = Math.min((o.workload_points / 10) * 100, 100)
                return (
                  <div key={i} style={{ marginBottom: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between",
                      marginBottom: "5px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "12px", color: "#d1d5db" }}>{o.name}</span>
                        {o.role === "Supervisor" && (
                          <Badge text="SUP" color="#fbbf24" bg="rgba(251,191,36,0.1)" />
                        )}
                      </div>
                      <span style={{ fontSize: "11px", color: "#6b7280",
                        fontFamily: "monospace" }}>
                        {o.skill} · {o.workload_points} pts
                      </span>
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.05)",
                      borderRadius: "4px", height: "6px" }}>
                      <div style={{ width: `${pct}%`, height: "100%",
                        background: c.accent, borderRadius: "4px",
                        transition: "width 0.5s ease" }} />
                    </div>
                  </div>
                )
              })}
            </div>

            <SectionHead title="Run History" />
            {stats.recent_runs.length === 0 && (
              <p style={{ color: "#4b5563", fontSize: "13px" }}>No runs yet.</p>
            )}
            {stats.recent_runs.map(r => (
              <div key={r.run_id} style={{ display: "flex", justifyContent: "space-between",
                alignItems: "center", padding: "10px 16px", borderRadius: "8px",
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
                marginBottom: "6px", fontSize: "12px", flexWrap: "wrap", gap: "8px" }}>
                <span style={{ color: "#60a5fa", fontFamily: "monospace" }}>#{r.run_id}</span>
                <span style={{ color: "#6b7280" }}>{r.run_at}</span>
                <span style={{ color: "#9ca3af" }}>{r.week_start || "—"}</span>
                <span style={{ color: "#34d399" }}>✓ {r.total_assigned}</span>
                <span style={{ color: r.total_unassigned > 0 ? "#f87171" : "#374151" }}>
                  ⚠ {r.total_unassigned}
                </span>
                <StatusPill status={r.status} />
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}
