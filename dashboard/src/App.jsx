import { useState, useRef } from 'react'
import './index.css'

const EXAMPLES = [
  'Pay electricity bill today',
  'Call dentist to schedule appointment',
  'Submit assignment by midnight',
  'Read a book for fun',
  'Fix critical bug before client demo',
  'Go for a walk',
]

const PRIORITY_ICONS = {
  High:   '🔴',
  Medium: '🟡',
  Low:    '🟢',
}

function PriorityBadge({ priority }) {
  const cls = priority?.toLowerCase()
  return (
    <span className={`priority-badge ${cls}`}>
      <span className="priority-dot" />
      {PRIORITY_ICONS[priority]} {priority} Priority
    </span>
  )
}

export default function App() {
  const [task, setTask]       = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [error, setError]     = useState(null)
  const [history, setHistory] = useState([])
  const inputRef              = useRef(null)

  // Derived stats
  const countHigh   = history.filter(h => h.priority === 'High').length
  const countMedium = history.filter(h => h.priority === 'Medium').length
  const countLow    = history.filter(h => h.priority === 'Low').length

  async function analyze(taskText) {
    const t = (taskText ?? task).trim()
    if (!t) return

    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const res  = await fetch(`/api/life-admin?task=${encodeURIComponent(t)}`)
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const json = await res.json()
      const data = json.result ?? json

      setResult(data)
      setHistory(prev => [
        { task: data.task, priority: data.priority, id: Date.now() },
        ...prev.slice(0, 9),           // keep last 10
      ])
      setTask('')
    } catch (err) {
      setError(err.message || 'Something went wrong. Is the ARIA server running?')
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter') analyze()
  }

  function handleHistory(item) {
    setTask(item.task)
    inputRef.current?.focus()
  }

  return (
    <>
      {/* ── Header ── */}
      <header className="aria-header">
        <div className="aria-logo-row">
          <div className="aria-logo-icon">🤖</div>
          <h1 className="aria-title">ARIA</h1>
        </div>
        <p className="aria-subtitle">
          AI-powered life admin assistant. Drop any task and ARIA will assess
          its priority and tell you exactly what to do next.
        </p>
      </header>

      {/* ── Input card ── */}
      <div className="input-card">
        <label className="input-label" htmlFor="task-input">What's on your mind?</label>
        <div className="input-row">
          <input
            id="task-input"
            ref={inputRef}
            className="task-input"
            type="text"
            placeholder="e.g. Pay rent before the deadline…"
            value={task}
            onChange={e => setTask(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
            autoComplete="off"
          />
          <button
            id="analyze-btn"
            className="analyze-btn"
            onClick={() => analyze()}
            disabled={loading || !task.trim()}
          >
            {loading ? '⏳' : '✨'} Analyze
          </button>
        </div>

        {/* Quick examples */}
        <div className="examples-row">
          {EXAMPLES.map(ex => (
            <button
              key={ex}
              className="example-chip"
              onClick={() => { setTask(ex); analyze(ex) }}
              disabled={loading}
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* ── Loading state ── */}
      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <p className="loading-text">ARIA is thinking…</p>
        </div>
      )}

      {/* ── Error ── */}
      {error && !loading && (
        <div className="error-card">
          <span className="error-icon">⚠️</span>
          <p className="error-text">{error}</p>
        </div>
      )}

      {/* ── Result ── */}
      {result && !loading && (
        <div className="result-card">
          <div className="result-header">
            <div>
              <p className="result-task-label">Your Task</p>
              <p className="result-task-text">{result.task}</p>
            </div>
            <PriorityBadge priority={result.priority} />
          </div>

          <div className="result-divider" />

          <p className="result-ai-label">
            <span className="ai-icon">🧠</span> ARIA's Analysis
          </p>
          <p className="result-message">{result.message}</p>
        </div>
      )}

      {/* ── Stats row ── */}
      {history.length > 0 && (
        <div className="stats-row">
          <div className="stat-chip">
            <span className="stat-value" style={{ color: 'var(--high)' }}>{countHigh}</span>
            <span className="stat-label">🔴 High Priority</span>
          </div>
          <div className="stat-chip">
            <span className="stat-value" style={{ color: 'var(--medium)' }}>{countMedium}</span>
            <span className="stat-label">🟡 Medium Priority</span>
          </div>
          <div className="stat-chip">
            <span className="stat-value" style={{ color: 'var(--low)' }}>{countLow}</span>
            <span className="stat-label">🟢 Low Priority</span>
          </div>
          <div className="stat-chip">
            <span className="stat-value">{history.length}</span>
            <span className="stat-label">✅ Tasks Analyzed</span>
          </div>
        </div>
      )}

      {/* ── History ── */}
      {history.length > 0 && (
        <section className="history-section">
          <p className="history-title">
            🕑 Recent Tasks
          </p>
          <div className="history-list">
            {history.map(item => (
              <div
                key={item.id}
                className="history-item"
                onClick={() => handleHistory(item)}
                role="button"
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && handleHistory(item)}
              >
                <span className="history-task">{item.task}</span>
                <span className={`history-badge ${item.priority?.toLowerCase()}`}>
                  {PRIORITY_ICONS[item.priority]} {item.priority}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  )
}
