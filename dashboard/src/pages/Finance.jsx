import { useState, useEffect, useCallback } from 'react'
import {
  TrendingUp, TrendingDown, Wallet, PiggyBank, Target, CreditCard,
  Plus, Trash2, Sparkles, ArrowUpRight, ArrowDownRight, Clock,
  Receipt, BarChart3, Brain, Settings, X, Save, RefreshCcw
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import '../styles/finance.css'

const API = '/api/finance'

const CATEGORIES = [
  'Food', 'Rent', 'Transport', 'Groceries', 'Shopping', 'Entertainment',
  'Utilities', 'Health', 'Subscriptions', 'EMI', 'Investments',
  'Education', 'Personal', 'Salary', 'Freelance', 'Other'
]

const CAT_COLORS = {
  Food: '#f97316', Rent: '#8b5cf6', Transport: '#3b82f6',
  Groceries: '#10b981', Shopping: '#ec4899', Entertainment: '#f43f5e',
  Utilities: '#06b6d4', Health: '#14b8a6', Subscriptions: '#a855f7',
  EMI: '#ef4444', Investments: '#6366f1', Education: '#0ea5e9',
  Personal: '#d946ef', Salary: '#22c55e', Freelance: '#84cc16', Other: '#64748b'
}

const fmt = (n) => {
  if (n === undefined || n === null) return '₹0'
  const abs = Math.abs(n)
  if (abs >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`
  if (abs >= 100000) return `₹${(n / 100000).toFixed(1)}L`
  return `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

export default function Finance() {
  const [summary, setSummary] = useState(null)
  const [categories, setCategories] = useState([])
  const [dailySpend, setDailySpend] = useState([])
  const [budgets, setBudgets] = useState([])
  const [goals, setGoals] = useState([])
  const [subs, setSubs] = useState([])
  const [transactions, setTransactions] = useState([])
  const [insights, setInsights] = useState([])
  const [txFilter, setTxFilter] = useState('all')
  const [toast, setToast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [nlText, setNlText] = useState('')
  const [nlLoading, setNlLoading] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [profile, setProfile] = useState({ monthly_income: '', rent: '', city: '' })

  // Manual form state
  const [form, setForm] = useState({
    amount: '', description: '', type: 'expense',
    category: 'Auto', payment_method: 'UPI', date: new Date().toISOString().split('T')[0]
  })

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [sumRes, catRes, dailyRes, budRes, goalRes, subRes, txRes, profRes] = await Promise.all([
        fetch(`${API}/summary`), fetch(`${API}/category-breakdown`),
        fetch(`${API}/daily-spending?days=30`), fetch(`${API}/budgets`),
        fetch(`${API}/goals`), fetch(`${API}/subscriptions`),
        fetch(`${API}/transactions?limit=50`), fetch(`${API}/profile`)
      ])
      setSummary(await sumRes.json())
      setCategories(await catRes.json())
      setDailySpend(await dailyRes.json())
      setBudgets(await budRes.json())
      setGoals(await goalRes.json())
      setSubs(await subRes.json())
      setTransactions(await txRes.json())
      const profData = await profRes.json()
      setProfile({
        monthly_income: profData.monthly_income || '',
        rent: profData.rent || '',
        city: profData.city || ''
      })
    } catch (e) {
      console.error('Fetch error:', e)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const fetchInsights = async () => {
    try {
      const res = await fetch(`${API}/insights`)
      const data = await res.json()
      setInsights(data.insights || [])
    } catch (e) { console.error(e) }
  }

  // ─── Natural Language Transaction ────────────
  const handleNL = async () => {
    if (!nlText.trim()) return
    setNlLoading(true)
    try {
      const res = await fetch(`${API}/transaction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: nlText })
      })
      const data = await res.json()
      if (data.error) {
        showToast(data.error, 'error')
      } else {
        showToast('Transaction added via AI!')
        setNlText('')
        fetchAll()
      }
    } catch (e) { showToast('Failed to add', 'error') }
    setNlLoading(false)
  }

  // ─── Manual Transaction ──────────────────────
  const handleManual = async (e) => {
    e.preventDefault()
    if (!form.amount || !form.description) return
    try {
      const res = await fetch(`${API}/transaction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, amount: parseFloat(form.amount) })
      })
      const data = await res.json()
      if (data.error) { showToast(data.error, 'error'); return }
      showToast(`${form.type === 'income' ? 'Income' : 'Expense'} added!`)
      setForm({ ...form, amount: '', description: '' })
      fetchAll()
    } catch (e) { showToast('Failed', 'error') }
  }



  const deleteTx = async (id) => {
    try {
      await fetch(`${API}/transaction/${id}`, { method: 'DELETE' })
      showToast('Deleted')
      fetchAll()
    } catch (e) { showToast('Failed', 'error') }
  }

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to delete ALL financial data? This cannot be undone.")) return
    try {
      await fetch(`${API}/reset`, { method: 'POST' })
      showToast('All data cleared')
      fetchAll()
    } catch (e) { showToast('Reset failed', 'error') }
  }

  const handleUpdateProfile = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch(`${API}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          monthly_income: parseFloat(profile.monthly_income) || 0,
          rent: parseFloat(profile.rent) || 0,
          city: profile.city
        })
      })
      if (res.ok) {
        showToast('Profile updated')
        setShowProfile(false)
        fetchAll()
      }
    } catch (e) { showToast('Update failed', 'error') }
  }

  const filteredTx = transactions.filter(tx =>
    txFilter === 'all' ? true : txFilter === tx.type
  )

  if (loading) {
    return (
      <div className="finance-page">
        <div className="empty-state">
          <div className="shimmer" style={{ margin: '0 auto 16px' }}></div>
          <p>Loading financial data...</p>
        </div>
      </div>
    )
  }

  const chartData = dailySpend.map(d => ({
    date: d.date.slice(5),
    amount: d.amount
  }))

  const pieData = categories.map(c => ({ name: c.category, value: c.amount }))

  return (
    <div className="finance-page">
      <div className="finance-header">
        <h2 className="section-title"><Wallet size={24} /> Financial Overview</h2>
        <div className="finance-header-actions">
          <button className="filter-chip" onClick={() => setShowProfile(true)}>
            <Settings size={14} style={{ bottom: "20px" }} /> Profile Settings
          </button>
          <button className="filter-chip reset-btn" onClick={handleReset}>
            <RefreshCcw size={14} /> Reset All Data
          </button>
        </div>
      </div>

      {showProfile && (
        <div className="quick-add-card profile-card">
          <div className="profile-header">
            <h3><Settings size={20} /> Profile Settings</h3>
            <button className="icon-btn" onClick={() => setShowProfile(false)}><X size={20} /></button>
          </div>
          <form onSubmit={handleUpdateProfile}>
            <div className="form-row">
              <div className="form-group">
                <label>Monthly Income (₹)</label>
                <input className="fin-input" type="number" value={profile.monthly_income}
                  onChange={e => setProfile({ ...profile, monthly_income: e.target.value })} placeholder="e.g. 85000" />
              </div>
              <div className="form-group">
                <label>Monthly Rent (₹)</label>
                <input className="fin-input" type="number" value={profile.rent}
                  onChange={e => setProfile({ ...profile, rent: e.target.value })} placeholder="e.g. 15000" />
              </div>
              <div className="form-group">
                <label>City</label>
                <input className="fin-input" type="text" value={profile.city}
                  onChange={e => setProfile({ ...profile, city: e.target.value })} placeholder="e.g. Bangalore" />
              </div>
            </div>
            <button type="submit" className="submit-btn" style={{ background: 'var(--fin-income)' }}>
              <Save size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Save Profile
            </button>
          </form>
        </div>
      )}
      {/* ──── Overview Cards ──── */}
      <div className="overview-grid">
        <div className="overview-card balance">
          <div className="ov-label"><Wallet size={14} /> Current Balance</div>
          <div className="ov-value">{fmt(summary?.balance)}</div>
          <div className={`ov-change ${summary?.balance >= 0 ? 'positive' : 'negative'}`}>
            {summary?.balance >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {summary?.savings_rate}% savings rate
          </div>
        </div>
        <div className="overview-card income">
          <div className="ov-label"><TrendingUp size={14} /> Income</div>
          <div className="ov-value">{fmt(summary?.income)}</div>
          <div className={`ov-change ${summary?.income_change >= 0 ? 'positive' : 'negative'}`}>
            {summary?.income_change >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {fmt(Math.abs(summary?.income_change || 0))} vs last month
          </div>
        </div>
        <div className="overview-card expense">
          <div className="ov-label"><TrendingDown size={14} /> Expenses</div>
          <div className="ov-value">{fmt(summary?.expenses)}</div>
          <div className={`ov-change ${summary?.expense_change <= 0 ? 'positive' : 'negative'}`}>
            {summary?.expense_change <= 0 ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
            {fmt(Math.abs(summary?.expense_change || 0))} vs last month
          </div>
        </div>
        <div className="overview-card savings">
          <div className="ov-label"><PiggyBank size={14} /> Rent Status</div>
          <div className="ov-value">{fmt(summary?.rent_amount)}</div>
          <div className={`ov-change ${summary?.rent_paid ? 'positive' : 'negative'}`}>
            {summary?.rent_paid ? '✅ Paid this month' : '⏳ Pending'}
          </div>
        </div>
      </div>

      {/* ──── Quick Add Transaction ──── */}
      <div className="quick-add-card">
        <h3><Plus size={20} /> Add Transaction</h3>
        <div className="nl-input-bar">
          <input className="nl-input" placeholder='Try: "Spent 450 on lunch at Zomato"'
            value={nlText} onChange={e => setNlText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleNL()} disabled={nlLoading} />
          <button className="nl-btn" onClick={handleNL} disabled={nlLoading || !nlText.trim()}>
            {nlLoading ? 'Parsing...' : '✨ AI Add'}
          </button>
        </div>
        <div className="or-divider">— or add manually —</div>
        <form onSubmit={handleManual}>
          <div className="form-row">
            <div className="form-group type-group">
              <label>Type</label>
              <div className="type-toggle">
                <button type="button"
                  className={`type-btn ${form.type === 'expense' ? 'active-expense' : ''}`}
                  onClick={() => setForm({ ...form, type: 'expense' })}>Expense</button>
                <button type="button"
                  className={`type-btn ${form.type === 'income' ? 'active-income' : ''}`}
                  onClick={() => setForm({ ...form, type: 'income' })}>Income</button>
              </div>
            </div>
            <div className="form-group amount-group">
              <label>Amount (₹)</label>
              <input className="fin-input amount-input" type="number" placeholder="0"
                value={form.amount} onChange={e => setForm({ ...form, amount: e.target.value })} />
            </div>
            <div className="form-group desc-group">
              <label>Description</label>
              <input className="fin-input" placeholder="What was it for?"
                value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Category</label>
              <select className="fin-select" value={form.category}
                onChange={e => setForm({ ...form, category: e.target.value })}>
                <option value="Auto">🤖 Auto-detect</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Payment</label>
              <select className="fin-select" value={form.payment_method}
                onChange={e => setForm({ ...form, payment_method: e.target.value })}>
                {['UPI', 'Cash', 'Card', 'NetBanking'].map(p =>
                  <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Date</label>
              <input className="fin-input" type="date" value={form.date}
                onChange={e => setForm({ ...form, date: e.target.value })} />
            </div>
          </div>
          <button type="submit" className="submit-btn"
            disabled={!form.amount || !form.description}>
            <Plus size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Add Transaction
          </button>
        </form>
      </div>

      {/* ──── Charts ──── */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3><BarChart3 size={18} /> Daily Spending (30 Days)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, color: '#fff' }}
                formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, 'Spent']} />
              <Area type="monotone" dataKey="amount" stroke="#f43f5e" strokeWidth={2}
                fill="url(#spendGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-card">
          <h3><Receipt size={18} /> Category Split</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                paddingAngle={3} dataKey="value" stroke="none">
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={CAT_COLORS[entry.name] || '#64748b'} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, color: '#fff' }}
                formatter={(v) => [`₹${v.toLocaleString('en-IN')}`, '']} />
              <Legend iconType="circle" iconSize={8}
                formatter={(v) => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ──── Budget Tracker ──── */}
      {budgets.length > 0 && (
        <div className="budget-section">
          <h3><Target size={18} /> Budget Tracker</h3>
          <div className="budget-grid">
            {budgets.map(b => {
              const pct = Math.min(b.percentage, 100)
              const status = b.percentage >= 90 ? 'danger' : b.percentage >= 70 ? 'warning' : 'safe'
              return (
                <div key={b.category} className="budget-item">
                  <div className="budget-header">
                    <span className="budget-cat">{b.category}</span>
                    <span className="budget-amounts">{fmt(b.spent)} / {fmt(b.monthly_limit)}</span>
                  </div>
                  <div className="budget-bar">
                    <div className={`budget-fill ${status}`} style={{ width: `${pct}%` }} />
                  </div>
                  <div className={`budget-pct ${status}`}>
                    {b.percentage.toFixed(0)}% • {fmt(b.remaining)} left
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ──── Savings Goals ──── */}
      {goals.length > 0 && (
        <>
          <h3 className="section-title"><PiggyBank size={18} /> Savings Goals</h3>
          <div className="goals-grid">
            {goals.map(g => {
              const pct = Math.min(g.progress, 100)
              const circumference = 2 * Math.PI * 28
              const offset = circumference - (pct / 100) * circumference
              return (
                <div key={g.id} className="goal-card">
                  <div className="goal-header">
                    <span className="goal-name">{g.name}</span>
                    <span className={`goal-priority ${g.priority}`}>{g.priority}</span>
                  </div>
                  <div className="goal-progress-ring">
                    <div className="ring-container">
                      <svg width="72" height="72">
                        <circle className="ring-bg" cx="36" cy="36" r="28" />
                        <circle className="ring-fill" cx="36" cy="36" r="28"
                          strokeDasharray={circumference}
                          strokeDashoffset={offset} />
                      </svg>
                      <span className="ring-text">{pct.toFixed(0)}%</span>
                    </div>
                    <div className="goal-amounts">
                      <div className="goal-current">{fmt(g.current_amount)}</div>
                      <div className="goal-target">of {fmt(g.target_amount)}</div>
                    </div>
                  </div>
                  {g.deadline && (
                    <div className="goal-deadline">
                      <Clock size={12} /> Deadline: {new Date(g.deadline).toLocaleDateString('en-IN', {
                        day: 'numeric', month: 'short', year: 'numeric'
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* ──── Subscriptions + AI Insights ──── */}
      <div className="bottom-grid">
        <div className="subs-section">
          <h3><CreditCard size={18} /> Subscriptions</h3>
          {subs.map(s => (
            <div key={s.id} className="sub-item">
              <div className="sub-info">
                <div className="sub-icon">💎</div>
                <div>
                  <div className="sub-name">{s.name}</div>
                  <div className="sub-freq">{s.frequency}</div>
                </div>
              </div>
              <span className="sub-amount">{fmt(s.amount)}</span>
            </div>
          ))}
          {subs.length > 0 && (
            <div className="sub-total">
              <span className="sub-total-label">Total Monthly</span>
              <span className="sub-total-amount">
                {fmt(subs.reduce((sum, s) => sum + (s.frequency === 'monthly' ? s.amount : s.frequency === 'yearly' ? s.amount / 12 : s.amount), 0))}
              </span>
            </div>
          )}
        </div>

        <div className="insights-section">
          <h3>
            <Sparkles size={18} /> AI Insights
            <button onClick={fetchInsights}
              style={{ marginLeft: 'auto', background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.3)', color: '#a78bfa', padding: '6px 14px', borderRadius: 10, fontSize: 11, fontWeight: 700, cursor: 'pointer' }}>
              Generate
            </button>
          </h3>
          {insights.length === 0 ? (
            <div className="empty-state">
              <Brain size={32} style={{ opacity: 0.3, marginBottom: 10 }} />
              <p>Click "Generate" for AI-powered financial insights</p>
            </div>
          ) : (
            insights.map((ins, i) => (
              <div key={i} className={`insight-card ${ins.type}`}>
                <div className="insight-header">
                  <span className="insight-icon">{ins.icon}</span>
                  <span className="insight-title">{ins.title}</span>
                </div>
                <div className="insight-msg">{ins.message}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ──── Transaction History ──── */}
      <div className="tx-section">
        <h3><Receipt size={18} /> Transaction History</h3>
        <div className="tx-filters">
          {['all', 'expense', 'income'].map(f => (
            <button key={f} className={`filter-chip ${txFilter === f ? 'active' : ''}`}
              onClick={() => setTxFilter(f)}>
              {f === 'all' ? 'All' : f === 'expense' ? '📉 Expenses' : '📈 Income'}
            </button>
          ))}
        </div>
        <div className="tx-list">
          {filteredTx.slice(0, 30).map(tx => (
            <div key={tx.id} className="tx-item">
              <div className="tx-left">
                <div className={`tx-cat-dot cat-${tx.category}`} />
                <div>
                  <div className="tx-desc">{tx.description}</div>
                  <div className="tx-meta">{tx.category} • {tx.payment_method}</div>
                </div>
              </div>
              <div className="tx-right-section">
                <div className="tx-right">
                  <div className={`tx-amount ${tx.type}`}>
                    {tx.type === 'income' ? '+' : '-'}{fmt(tx.amount)}
                  </div>
                  <div className="tx-date-label">{tx.date}</div>
                </div>
                <button className="tx-del-btn" onClick={() => deleteTx(tx.id)}>
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
          {filteredTx.length === 0 && (
            <div className="empty-state">No transactions found.</div>
          )}
        </div>
      </div>

      {/* ──── Toast ──── */}
      {toast && <div className={`fin-toast ${toast.type}`}>{toast.msg}</div>}
    </div>
  )
}
