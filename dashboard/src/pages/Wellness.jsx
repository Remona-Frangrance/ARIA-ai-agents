import { useState, useEffect } from 'react'
import { Activity, Moon, Droplets, Smile, Zap, Plus, Brain, TrendingUp, Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import '../styles/wellness.css'


export default function Wellness() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [hydration, setHydration] = useState(5)
  const [sleepInput, setSleepInput] = useState('')

  useEffect(() => {
    fetch('/api/wellness/analytics')
      .then(res => res.json())
      .then(json => {
        setData(json)
        setLoading(false)
        // Set hydration to last logged value
        const lastHydro = json.logs.find(l => l.type === 'hydration')
        if (lastHydro) setHydration(lastHydro.value)
      })
  }, [])

  const logWater = async () => {
    setHydration(h => h + 1)
    await fetch('/api/wellness?task=Logged 1 glass of water')
  }

  const logSleep = async () => {
    if (!sleepInput || isNaN(sleepInput)) return
    await fetch(`/api/wellness?task=I slept for ${sleepInput} hours`)
    setSleepInput('')
    // Refresh
    const refresh = await fetch('/api/wellness/analytics')
    const newData = await refresh.json()
    setData(newData)
  }

  const [journal, setJournal] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [moodResult, setMoodResult] = useState(null)

  const handleMoodAnalysis = async () => {
    if (!journal.trim()) return
    setAnalyzing(true)
    try {
      const res = await fetch(`/api/wellness?task=${encodeURIComponent(journal)}`)
      const json = await res.json()
      setMoodResult(json.result)
      setJournal('')
      // Refresh analytics to show new mood point
      const refresh = await fetch('/api/wellness/analytics')
      const newData = await refresh.json()
      setData(newData)
    } catch (e) { console.error(e) }
    setAnalyzing(false)
  }

  if (loading) return <div className="loading-overlay"><div className="shimmer"></div><p>Syncing Biological Data...</p></div>

  const sleepData = data.logs.filter(l => l.type === 'sleep').slice(0, 7).reverse().map(l => ({
    day: new Date(l.date).toLocaleDateString('en-US', { weekday: 'short' }),
    hours: l.value
  }))

  const moodData = data.logs.filter(l => l.type === 'mood').slice(0, 5).reverse().map(l => ({
    time: new Date(l.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    score: l.value
  }))

  const goal = 8
  const pct = Math.min((hydration / goal) * 100, 100)
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="wellness-page">
      <div className="wellness-grid">
        {/* --- Sleep Analysis --- */}
        <div className="well-card">
          <div className="well-header">
            <div className="well-icon" style={{ background: 'rgba(129, 140, 248, 0.1)', color: '#818cf8' }}>
              <Moon size={20} />
            </div>
            <span className="well-title">Sleep Quality</span>
          </div>
          <div className="tracker-row">
            <div>
              <span className="tracker-value">{(sleepData.reduce((acc, s) => acc + s.hours, 0) / sleepData.length || 0).toFixed(1)}</span>
              <span className="tracker-unit">avg hrs</span>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="number" 
                className="well-input" 
                style={{ width: '60px', marginTop: 0, padding: '8px' }}
                placeholder="Hrs"
                value={sleepInput}
                onChange={e => setSleepInput(e.target.value)}
              />
              <button className="well-btn" style={{ marginTop: 0, padding: '8px 12px' }} onClick={logSleep}>
                <Plus size={16} />
              </button>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sleepData}>
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '12px' }} />
                <Bar dataKey="hours" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* --- Hydration Tracker --- */}
        <div className="well-card">
          <div className="well-header">
            <div className="well-icon" style={{ background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8' }}>
              <Droplets size={20} />
            </div>
            <span className="well-title">Hydration</span>
          </div>
          <div className="progress-container">
            <svg width="120" height="120" style={{ transform: 'rotate(-90deg)' }}>
              <circle className="progress-ring-bg" cx="60" cy="60" r="45" />
              <circle 
                className="progress-ring-fill" 
                cx="60" cy="60" r="45"
                stroke="#38bdf8"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
              />
            </svg>
            <div className="progress-text">
              <span className="progress-pct">{hydration}</span>
              <span style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase' }}>Glasses</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button className="well-btn" style={{ flex: 1, marginTop: 0 }} onClick={logWater}>
              <Plus size={16} /> Add Water
            </button>
            <button className="well-btn" style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', marginTop: 0 }} onClick={() => setHydration(0)}>
              Reset
            </button>
          </div>
        </div>

        {/* --- Mood Check-in --- */}
        <div className="well-card checkin-section">
          <div className="well-header">
            <div className="well-icon" style={{ background: 'rgba(244, 114, 182, 0.1)', color: '#f472b6' }}>
              <Smile size={20} />
            </div>
            <span className="well-title">Daily Journal</span>
          </div>
          <p style={{ fontSize: '13px', opacity: 0.8 }}>How are you feeling mentally today?</p>
          <textarea 
            className="well-input" 
            placeholder="Write a few lines about your day..."
            rows="3"
            value={journal}
            onChange={e => setJournal(e.target.value)}
          />
          <button 
            className="well-btn" 
            style={{ background: '#f472b6', color: '#fff', width: '100%' }}
            onClick={handleMoodAnalysis}
            disabled={analyzing || !journal.trim()}
          >
            <Brain size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} />
            {analyzing ? 'Analyzing...' : 'AI Mood Analysis'}
          </button>
          
          {moodResult && (
            <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', fontSize: '12px' }}>
              <strong>Result:</strong> {moodResult.message}
            </div>
          )}
        </div>
      </div>

      <div className="wellness-grid">
        {/* --- Mood Trends --- */}
        <div className="well-card" style={{ gridColumn: 'span 2' }}>
          <div className="well-header">
            <div className="well-icon" style={{ background: 'rgba(45, 212, 191, 0.1)', color: '#2dd4bf' }}>
              <TrendingUp size={20} />
            </div>
            <span className="well-title">Emotional Vitality (History)</span>
          </div>
          <div className="chart-container" style={{ height: '150px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={moodData}>
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '12px' }} />
                <Line type="monotone" dataKey="score" stroke="#2dd4bf" strokeWidth={3} dot={{ fill: '#2dd4bf' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* --- Burnout Alert --- */}
        <div className="well-card" style={{ borderLeft: `4px solid ${data.burnout.risk === 'High' ? '#ef4444' : '#fb923c'}` }}>
          <div className="well-header">
            <div className="well-icon" style={{ background: 'rgba(251, 146, 60, 0.1)', color: '#fb923c' }}>
              <Zap size={20} />
            </div>
            <span className="well-title">Burnout Risk (AI Model)</span>
          </div>
          <div style={{ padding: '12px', background: 'rgba(251, 146, 60, 0.05)', borderRadius: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fb923c', fontWeight: '700', marginBottom: '8px' }}>
              <Info size={16} /> {data.burnout.risk} Risk ({data.burnout.score}%)
            </div>
            <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: '1.5' }}>
              {data.burnout.reason}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
