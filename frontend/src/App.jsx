import { useState, useEffect } from 'react'
import { sendChatMessage, fetchDashboardRequests, runRegulatoryRadar, analyzeDocument } from './api'
import ReactMarkdown from 'react-markdown'

function ScopeBadge({ inScope }) {
  return (
    <span className={`badge ${inScope ? 'badge-green' : 'badge-red'}`}>
      {inScope ? 'IN SCOPE' : 'OUT OF SCOPE'}
    </span>
  )
}

function ChatPanel({ onNewResult }) {
  const [message, setMessage] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!message.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await sendChatMessage(message)
      setResult(data)
      onNewResult()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Ask ZenAI</h2>
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="e.g. What are our Scope 1 emissions?"
        />
        <button type="submit" disabled={loading}>{loading ? 'Thinking...' : 'Send'}</button>
      </form>

      {error && <p className="error">Error: {error}</p>}

      {result && (
        <div className="result-card">
          <div className="result-header">
            <ScopeBadge inScope={result.in_scope} />
            {result.action_taken && <span className="action-tag">{result.action_taken}</span>}
          </div>

          <p><strong>Scope reason:</strong> {result.scope_reason}</p>
          {result.matched_keywords?.length > 0 && (
            <p><strong>Matched keywords:</strong> {result.matched_keywords.join(', ')}</p>
          )}
          {result.request_type && <p><strong>Request type:</strong> {result.request_type}</p>}
          {result.model_used && (
            <p><strong>Model used:</strong> {result.model_used} — <em>{result.model_reason}</em></p>
          )}
          {result.sources?.length > 0 && (
            <p><strong>Sources:</strong> {[...new Set(result.sources)].join(', ')}</p>
          )}
          <p><strong>Validation:</strong> {result.validation_passed ? 'PASSED' : 'FLAGGED'}</p>

          <div className="response-box">
            <strong>Response:</strong>
            <div className="markdown-content"><ReactMarkdown>{result.response}</ReactMarkdown></div>
          </div>
        </div>
      )}
    </div>
  )
}

function DocumentPanel({ onNewResult }) {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    try {
      const data = await analyzeDocument(file)
      setResult(data)
      onNewResult()
    } catch (err) {
      setResult({ analysis: `Error: ${err.message}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Document Analysis</h2>
      <form onSubmit={handleUpload} className="chat-form">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit" disabled={loading || !file}>{loading ? 'Analyzing...' : 'Upload & Analyze'}</button>
      </form>
      {result && (
        <div className="result-card">
          <p><strong>Chunks ingested:</strong> {result.chunks_ingested}</p>
          <div className="response-box">
            <strong>Analysis:</strong>
            <div className="markdown-content"><ReactMarkdown>{result.response}</ReactMarkdown></div>
          </div>
        </div>
      )}
    </div>
  )
}

function RegulatoryRadarPanel() {
  const [alerts, setAlerts] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleRun() {
    setLoading(true)
    try {
      const data = await runRegulatoryRadar()
      setAlerts(data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Regulatory Radar</h2>
      <button onClick={handleRun} disabled={loading}>{loading ? 'Running pipeline...' : 'Run Regulatory Radar'}</button>

      {alerts && (
        <div className="result-card">
          <p><strong>Ingested:</strong> {alerts.total_ingested} | <strong>Relevant:</strong> {alerts.relevant_count}</p>
          {alerts.alerts.filter(a => a.is_relevant).map((a, i) => (
            <div key={i} className="alert-item">
              <h4>{a.title}</h4>
              <p><strong>Keywords:</strong> {a.matched_keywords.slice(0, 5).join(', ')}</p>
              <p><strong>Impact:</strong> {a.impact_analysis}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ReviewDashboard({ refreshKey }) {
  const [requests, setRequests] = useState([])

  useEffect(() => {
    fetchDashboardRequests(20).then(setRequests).catch(() => setRequests([]))
  }, [refreshKey])

  return (
    <div className="panel">
      <h2>Review Interface — Recent Requests</h2>
      <div className="dashboard-table-wrapper">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>Request</th><th>Scope</th><th>Type</th><th>Model</th><th>Sources</th><th>Validation</th><th>Action</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id}>
                <td>{r.request_text}</td>
                <td><ScopeBadge inScope={r.in_scope} /></td>
                <td>{r.request_type || '-'}</td>
                <td>{r.model_used || '-'}</td>
                <td>{[...new Set(r.retrieved_sources || [])].join(', ') || '-'}</td>
                <td>{r.validation_passed === null || r.validation_passed === undefined ? '—' : (r.validation_passed ? 'PASS' : 'FLAG')}</td>
                <td>{r.action_taken}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)
  const triggerRefresh = () => setRefreshKey((k) => k + 1)

  return (
    <div className="app">
      <header>
        <h1>ZenAI Agent</h1>
        <p className="subtitle">Zenlynx Technology — Sustainability AI Orchestrator</p>
      </header>

      <main>
        <ChatPanel onNewResult={triggerRefresh} />
        <DocumentPanel onNewResult={triggerRefresh} />
        <RegulatoryRadarPanel />
        <ReviewDashboard refreshKey={refreshKey} />
      </main>
    </div>
  )
}