import { useState, useRef, useEffect } from 'react'
import { Check, Trash2, Calendar, LayoutDashboard, Brain, Wallet, Sparkles, Heart, Activity, Search, Trash, CheckCircle2 } from 'lucide-react'
import Finance from './pages/Finance'
import Wellness from './pages/Wellness'
import Relationships from './pages/Relationships'
import './index.css'

const AGENTS = [
  { id: 'life-admin', name: 'Life Admin', icon: <LayoutDashboard size={20} />, desc: 'Bills, deadlines, calendar, subscriptions' },
  { id: 'wellness', name: 'Wellness', icon: <Activity size={20} />, desc: 'Sleep, mood, hydration, burnout alerts' },
  { id: 'finance', name: 'Finance', icon: <Wallet size={20} />, desc: 'Spending, investments, market updates' },
  { id: 'content', name: 'Content', icon: <Sparkles size={20} />, desc: 'Posting schedule, analytics, trends', disabled: true },
  { id: 'relationships', name: 'Relationships', icon: <Heart size={20} />, desc: 'Birthdays, follow-ups, unanswered messages' },
]

const EXAMPLES = [
  'I feel a bit burnt out and tired today',
  'Remind me it is Sarah birthday on June 15th',
  'I drank 5 glasses of water today',
  'Suggest a gift for my tech-savvy brother',
  'How can I improve my sleep quality?',
]

export default function App() {
  const [activeAgent, setActiveAgent] = useState('life-admin')
  const [activeTab, setActiveTab] = useState('active')
  const [task, setTask] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('aria_task_history')
    return saved ? JSON.parse(saved) : []
  })
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    localStorage.setItem('aria_task_history', JSON.stringify(history))
  }, [history])

  async function handleAction(overrideTask) {
    const t = (overrideTask ?? task).trim()
    if (!t) return

    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const endpoint = activeAgent === 'life-admin' ? '/api/life-admin' : `/api/${activeAgent}`
      const res = await fetch(`${endpoint}?task=${encodeURIComponent(t)}`)
      
      if (!res.ok) throw new Error(`Server error ${res.status}`)
      
      const json = await res.json()
      const data = json.result ?? json
      
      setResult(data)
      
      if (data.type === 'task' || data.type === 'calendar') {
        const newEntry = {
          ...data,
          id: Date.now(),
          timestamp: new Date().toISOString(),
          agent: activeAgent,
          completed: false
        }
        setHistory(prev => [newEntry, ...prev])
      }
      
      if (!overrideTask) setTask('')
    } catch (err) {
      setError(err.message || 'Connection failed. Is the ARIA server running?')
    } finally {
      setLoading(false)
    }
  }

  function toggleComplete(id) {
    setHistory(prev => prev.map(item => 
      item.id === id ? { ...item, completed: !item.completed } : item
    ))
  }

  function deleteItem(id) {
    setHistory(prev => prev.filter(item => item.id !== id))
  }

  function clearAll() {
    if (window.confirm('Clear all tasks?')) setHistory([])
  }

  const filteredHistory = history.filter(item => 
    activeTab === 'completed' ? item.completed : !item.completed
  )

  const groupedHistory = filteredHistory.reduce((groups, item) => {
    const date = new Date(item.timestamp).toLocaleDateString('en-US', { 
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
    })
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
    return groups
  }, {})

  return (
    <div className="app-container">
      <div className="bg-glow"></div>
      <aside className="sidebar">
        <div className="logo-section">
          <img src="/logo.png" alt="ARIA Logo" className="logo-img" />
          <span className="logo-text">ARIA</span>
        </div>

        <nav className="nav-group">
          {AGENTS.map(agent => (
            <button
              key={agent.id}
              className={`nav-item ${activeAgent === agent.id ? 'active' : ''} ${agent.disabled ? 'disabled' : ''}`}
              onClick={() => !agent.disabled && setActiveAgent(agent.id)}
              disabled={agent.disabled}
            >
              <span className="nav-icon">{agent.icon}</span>
              <span className="nav-text">{agent.name}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>System Online</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="view-header">
          <h1 className="view-title">
            {AGENTS.find(a => a.id === activeAgent)?.name}
          </h1>
          <p className="view-desc">{AGENTS.find(a => a.id === activeAgent)?.desc}</p>
        </header>

        {activeAgent === 'finance' ? (
          <Finance />
        ) : activeAgent === 'wellness' ? (
          <Wellness />
        ) : activeAgent === 'relationships' ? (
          <Relationships />
        ) : (
          <>
            <section className="card">
              <div className="input-section">
                <div className="input-wrapper">
                  <div className="input-icon"><Brain size={20} /></div>
                  <input
                    ref={inputRef}
                    className="main-input"
                    placeholder="What can I help you with?"
                    value={task}
                    onChange={e => setTask(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleAction()}
                    disabled={loading}
                  />
                  <button
                    className="action-btn"
                    onClick={() => handleAction()}
                    disabled={loading || !task.trim()}
                  >
                    {loading ? 'Thinking...' : 'Analyze'}
                  </button>
                </div>

                <div className="examples-grid">
                  {EXAMPLES.map(ex => (
                    <div key={ex} className="example-card" onClick={() => { setTask(ex); handleAction(ex); }}>
                      {ex}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {loading && (
              <div className="loading-overlay">
                <div className="shimmer"></div>
                <p>ARIA is processing...</p>
              </div>
            )}

            {error && (
              <div className="card" style={{ borderColor: 'var(--high)', background: 'rgba(239, 68, 68, 0.05)' }}>
                <p style={{ color: 'var(--high)' }}>⚠️ {error}</p>
              </div>
            )}

            {result && !loading && (
              <div className="result-container">
                <ResultRenderer result={result} />
              </div>
            )}

            <section className="timeline-section">
              <div className="timeline-header-row">
                <h2 className="timeline-title"><Calendar size={24} color="var(--accent-primary)" /> Task Timeline</h2>
                <div className="tab-group">
                  <button 
                    className={`tab-btn ${activeTab === 'active' ? 'active' : ''}`}
                    onClick={() => setActiveTab('active')}
                  >
                    Active
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'completed' ? 'active' : ''}`}
                    onClick={() => setActiveTab('completed')}
                  >
                    Completed
                  </button>
                </div>
                {history.length > 0 && (
                  <button className="clear-btn" onClick={clearAll}>
                    <Trash size={14} /> Clear All
                  </button>
                )}
              </div>

              {filteredHistory.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '60px' }}>
                  {activeTab === 'completed' ? 'No completed tasks yet.' : 'Your timeline is empty.'}
                </p>
              ) : (
                Object.entries(groupedHistory).map(([date, items]) => (
                  <div key={date} className="timeline-group">
                    <div className="timeline-date">{date}</div>
                    <div className="timeline-items">
                      {items.map(item => (
                        <div key={item.id} className={`timeline-card ${item.completed ? 'completed' : ''}`}>
                          <div className="timeline-card-header">
                            <div className="timeline-card-info">
                              <span className="timeline-time">
                                {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                              <span className="category-tag">{item.category || 'Task'}</span>
                            </div>
                            <div className="timeline-card-actions">
                              <button 
                                className={`icon-btn done-btn ${item.completed ? 'undo' : ''}`} 
                                onClick={() => toggleComplete(item.id)}
                                title={item.completed ? 'Mark as Active' : 'Mark as Done'}
                              >
                                <CheckCircle2 size={18} />
                              </button>
                              <button 
                                className="icon-btn del-btn" 
                                onClick={() => deleteItem(item.id)}
                                title="Delete Task"
                              >
                                <Trash2 size={18} />
                              </button>
                            </div>
                          </div>
                          <div className="timeline-task-text">{item.task || item.result}</div>
                          {item.due_date && <div className="due-tag">⏳ Due: {item.due_date}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </section>
          </>
        )}
      </main>
    </div>
  )
}

function ResultRenderer({ result }) {
  const type = result.type || 'task'

  if (type === 'task') {
    return (
      <div className="card result-card-glow">
        <div className="result-header">
          <div className="result-tags">
            <span className="result-type-tag">Analysis</span>
            <span className="category-tag-large">{result.category}</span>
          </div>
          <span className={`priority-badge priority-${result.priority?.toLowerCase()}`}>
            {result.priority} Priority
          </span>
        </div>
        
        <h2 className="result-title">{result.task}</h2>
        {result.due_date && <div className="due-date-display">📅 Target: {result.due_date}</div>}
        
        <div className="ai-message">
          {result.message}
        </div>

        {result.steps && result.steps.length > 0 && (
          <div className="steps-section">
            <h3>Actionable Steps:</h3>
            <ul>
              {result.steps.map((step, i) => <li key={i}>{step}</li>)}
            </ul>
          </div>
        )}
      </div>
    )
  }

  if (type === 'calendar') {
    return (
      <div className="card result-card-glow">
        <span className="result-type-tag">Calendar Event</span>
        <div className="ai-message" style={{ fontSize: '20px', fontWeight: '600' }}>
          {result.result}
        </div>
        <div className="steps-section">
           <ul>
             <li>Opening Google Calendar...</li>
             <li>Review details and click 'Save' to confirm.</li>
           </ul>
        </div>
      </div>
    )
  }

  if (type === 'email') {
    return (
      <div className="card result-card-glow">
        <span className="result-type-tag">Gmail Action</span>
        <div className="ai-message">
          {result.result}
        </div>
      </div>
    )
  }

  if (type === 'wellness') {
    return (
      <div className="card result-card-glow wellness-card">
        <div className="result-header">
          <div className="result-tags">
            <span className="result-type-tag">Wellness Analysis</span>
            <span className="category-tag-large">{result.wellness_type}</span>
          </div>
          <span className={`sentiment-badge sentiment-${result.sentiment?.toLowerCase()}`}>
            {result.sentiment} Mood
          </span>
        </div>
        
        <div className="wellness-score-section">
           <div className="score-circle">
             <span className="score-value">{result.score}</span>
             <span className="score-label">Wellness Score</span>
           </div>
        </div>

        <div className="ai-message">
          {result.message}
        </div>

        {result.steps && result.steps.length > 0 && (
          <div className="steps-section">
            <h3>Actionable Advice:</h3>
            <ul>
              {result.steps.map((step, i) => <li key={i}>{step}</li>)}
            </ul>
          </div>
        )}
      </div>
    )
  }

  if (type === 'relationship') {
    return (
      <div className="card result-card-glow relationship-card">
        <div className="result-header">
          <div className="result-tags">
            <span className="result-type-tag">Social Intel</span>
            <span className="category-tag-large">{result.rel_type}</span>
          </div>
          {result.person && <span className="person-tag">👤 {result.person}</span>}
        </div>
        
        {result.event_date && (
          <div className="milestone-alert">
            📅 Upcoming Milestone: <strong>{result.event_date}</strong>
          </div>
        )}

        <div className="ai-message">
          {result.message}
        </div>

        {result.steps && result.steps.length > 0 && (
          <div className="steps-section">
            <h3>Social Suggestions:</h3>
            <ul>
              {result.steps.map((step, i) => <li key={i}>{step}</li>)}
            </ul>
          </div>
        )}
      </div>
    )
  }

  if (type === 'email_advanced') {
    const data = result.result
    return (
      <div className="card result-card-glow">
        <span className="result-type-tag">Inbox Intelligence</span>
        
        <div className="email-grid">
          <div className="email-category">
            <div className="category-title">🔴 Important</div>
            {data.important.map((m, i) => <div key={i} className="email-item important">{m}</div>)}
            {data.important.length === 0 && <p style={{ fontSize: '13px', opacity: 0.5 }}>No critical emails.</p>}
          </div>

          <div className="email-category">
            <div className="category-title">🟡 Promotions</div>
            {data.promotion.map((m, i) => <div key={i} className="email-item promotion">{m}</div>)}
          </div>

          <div className="email-category">
            <div className="category-title">⚪ Spam</div>
            {data.spam.map((m, i) => <div key={i} className="email-item spam">{m}</div>)}
          </div>
        </div>
      </div>
    )
  }

  return <div className="card">Unknown result type</div>
}
