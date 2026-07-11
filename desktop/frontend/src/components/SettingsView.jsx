import { useEffect, useRef, useState } from 'react'
import { fetchSettings, saveSettings, testConnection, fetchLLMLogs, clearLLMLogs } from '../api'

const VIEW_CSS = `
.cf-field {
  margin-bottom: 22px;
}
.cf-field-label {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--accent2);
  letter-spacing: 0.08em;
  display: block;
  margin-bottom: 8px;
}
.cf-input {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--rule2);
  border-radius: 8px;
  padding: 12px 14px;
  font-family: var(--font-mono);
  font-size: 0.92rem;
  color: var(--ink);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.cf-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(201, 169, 110, 0.15);
}
.cf-input::placeholder {
  color: #5d626c;
}
.cf-status {
  background: var(--bg2);
  border: 1px solid var(--rule);
  border-radius: 8px;
  padding: 14px 18px;
  font-size: 0.94rem;
  margin-bottom: 28px;
}
.cf-status.mock {
  border-left: 3px solid var(--muted);
  color: var(--muted);
}
.cf-status.real {
  border-left: 3px solid var(--accent2);
  color: var(--ink);
}
.cf-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-top: 8px;
}
.cf-msg {
  font-size: 0.9rem;
}
.cf-msg.ok { color: var(--accent2); }
.cf-msg.err { color: var(--danger); }

/* ===== LLM 调用日志面板 ===== */
.cf-logs {
  margin-top: 48px;
  padding-top: 28px;
  border-top: 1px solid var(--rule);
}
.cf-logs-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.cf-logs-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--accent);
}
.cf-logs-meta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--muted);
  letter-spacing: 0.06em;
  display: flex;
  align-items: center;
  gap: 10px;
}
.cf-logs-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent2);
  animation: cfpulse 1.5s ease-in-out infinite;
}
@keyframes cfpulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
.cf-log-item {
  background: var(--bg2);
  border: 1px solid var(--rule);
  border-radius: 8px;
  margin-bottom: 10px;
  overflow: hidden;
}
.cf-log-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.cf-log-row:hover {
  background: var(--bg3);
}
.cf-log-status {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  padding: 3px 9px;
  border-radius: 99px;
  letter-spacing: 0.04em;
  white-space: nowrap;
  border: 1px solid;
}
.cf-log-status.running {
  color: var(--accent);
  border-color: var(--accent);
  animation: cfpulse 1.2s ease-in-out infinite;
}
.cf-log-status.success {
  color: var(--accent2);
  border-color: var(--accent2);
}
.cf-log-status.failed,
.cf-log-status.timeout {
  color: var(--danger);
  border-color: var(--danger);
}
.cf-log-model {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: var(--ink);
  min-width: 0;
  flex: 0 1 auto;
}
.cf-log-model.mock {
  color: var(--muted);
}
.cf-log-stats {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--muted);
  margin-left: auto;
  white-space: nowrap;
}
.cf-log-detail {
  padding: 0 16px 16px;
  border-top: 1px solid var(--rule);
  animation: fadeUp 0.2s ease both;
}
.cf-log-field {
  margin-top: 12px;
}
.cf-log-field-label {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  color: var(--accent2);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: block;
  margin-bottom: 6px;
}
.cf-log-field-text {
  font-size: 0.86rem;
  color: var(--ink);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--bg);
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 10px 12px;
  font-family: var(--font-mono);
}
.cf-log-field-text.error {
  color: var(--danger);
  border-color: rgba(217, 138, 138, 0.35);
}
.cf-logs-empty {
  color: var(--muted);
  font-size: 0.9rem;
  padding: 24px 0;
  text-align: center;
}
`

export default function SettingsView({ onBack }) {
  const [baseUrl, setBaseUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('')
  const [mockMode, setMockMode] = useState(null) // null = unknown
  const [statusModel, setStatusModel] = useState('')

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)

  const [testing, setTesting] = useState(false)
  const [testMsg, setTestMsg] = useState(null) // { ok, text }
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null) // { ok, text }

  // LLM 调用日志面板状态
  const [logs, setLogs] = useState([])
  const [expandedId, setExpandedId] = useState(null)
  const logsTimer = useRef(null)

  useEffect(() => {
    let alive = true
    setLoading(true)
    setLoadError(null)
    fetchSettings()
      .then((s) => {
        if (!alive) return
        setBaseUrl(s.base_url || '')
        setApiKey(s.api_key || '')
        setModel(s.model || '')
        setStatusModel(s.model || '')
        setMockMode(!!s.mock_mode)
      })
      .catch((e) => {
        if (alive) setLoadError(e.message || '获取设置失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  // 轮询 LLM 调用日志：每 1.5s 拉取一次，实时展示模型输入输出与异常状态
  useEffect(() => {
    let alive = true
    async function poll() {
      try {
        const res = await fetchLLMLogs()
        if (alive) setLogs(res.logs || [])
      } catch {
        // 静默失败，不打断设置页
      }
    }
    poll()
    logsTimer.current = setInterval(poll, 1500)
    return () => {
      alive = false
      if (logsTimer.current) clearInterval(logsTimer.current)
    }
  }, [])

  async function handleClearLogs() {
    try {
      await clearLLMLogs()
      setLogs([])
      setExpandedId(null)
    } catch {
      /* ignore */
    }
  }

  async function handleTest() {
    setTesting(true)
    setTestMsg(null)
    try {
      const res = await testConnection({
        base_url: baseUrl,
        api_key: apiKey,
        model,
      })
      if (res.ok) {
        setTestMsg({
          ok: true,
          text: res.response ? `连接成功：${res.response}` : '连接成功',
        })
      } else {
        setTestMsg({ ok: false, text: res.error || '连接失败' })
      }
    } catch (e) {
      setTestMsg({ ok: false, text: e.message || '连接失败' })
    } finally {
      setTesting(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setSaveMsg(null)
    try {
      const res = await saveSettings({
        base_url: baseUrl,
        api_key: apiKey,
        model,
      })
      if (res.ok) {
        setMockMode(!!res.mock_mode)
        setStatusModel(model)
        setSaveMsg({ ok: true, text: '已保存' })
      } else {
        setSaveMsg({ ok: false, text: '保存失败' })
      }
    } catch (e) {
      setSaveMsg({ ok: false, text: e.message || '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="results">
      <style>{VIEW_CSS}</style>

      <div style={{ marginBottom: 20 }}>
        <button className="btn btn-ghost" onClick={onBack}>← 返回</button>
      </div>

      <header className="results-header">
        <span className="badge">设置 · LLM 接入</span>
        <h2>设置 · LLM 接入</h2>
      </header>

      {loading && (
        <div className="loading">
          <div className="spinner" />
          <p>正在读取配置…</p>
        </div>
      )}

      {loadError && (
        <div className="error-box big">
          <div>
            <strong>读取设置失败</strong>
            <div className="muted" style={{ marginTop: 4 }}>{loadError}</div>
          </div>
        </div>
      )}

      {!loading && !loadError && (
        <section className="module">
          {mockMode !== null && (
            <div className={mockMode ? 'cf-status mock' : 'cf-status real'}>
              {mockMode
                ? '当前为 mock 模式，填写 API Key 启用真实 LLM'
                : `已启用真实 LLM（${statusModel || model || '—'}）`}
            </div>
          )}

          <div className="cf-field">
            <label className="cf-field-label" htmlFor="cf-base-url">API Base URL</label>
            <input
              id="cf-base-url"
              className="cf-input"
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
              autoComplete="off"
            />
          </div>

          <div className="cf-field">
            <label className="cf-field-label" htmlFor="cf-api-key">API Key</label>
            <input
              id="cf-api-key"
              className="cf-input"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              autoComplete="off"
            />
          </div>

          <div className="cf-field">
            <label className="cf-field-label" htmlFor="cf-model">Model</label>
            <input
              id="cf-model"
              className="cf-input"
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gpt-4o-mini"
              autoComplete="off"
            />
          </div>

          <div className="cf-actions">
            <button
              className="btn btn-ghost"
              onClick={handleTest}
              disabled={testing || saving}
            >
              {testing ? '测试中…' : '测试连接'}
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={testing || saving}
            >
              {saving ? '保存中…' : '保存配置'}
            </button>
            {testMsg && (
              <span className={testMsg.ok ? 'cf-msg ok' : 'cf-msg err'}>
                {testMsg.text}
              </span>
            )}
            {saveMsg && (
              <span className={saveMsg.ok ? 'cf-msg ok' : 'cf-msg err'}>
                {saveMsg.text}
              </span>
            )}
          </div>
        </section>
      )}

      {/* ===== LLM 调用日志面板（实时轮询）===== */}
      <section className="cf-logs">
        <div className="cf-logs-head">
          <span className="cf-logs-title">LLM 调用日志</span>
          <div className="cf-logs-meta">
            <span className="cf-logs-pulse" />
            <span>实时刷新 · 1.5s</span>
            <button
              className="btn btn-ghost"
              onClick={handleClearLogs}
              disabled={logs.length === 0}
            >
              清空
            </button>
          </div>
        </div>

        {logs.length === 0 ? (
          <p className="cf-logs-empty">
            暂无调用记录。开始研究流程后，此处将实时显示每次 LLM 调用的输入、输出与状态。
          </p>
        ) : (
          logs.map((log) => (
            <div className="cf-log-item" key={log.call_id}>
              <div
                className="cf-log-row"
                onClick={() =>
                  setExpandedId(expandedId === log.call_id ? null : log.call_id)
                }
              >
                <span className={`cf-log-status ${log.status}`}>
                  {log.status === 'running' ? '输出中' : log.status}
                </span>
                <span className={`cf-log-model ${log.mock ? 'mock' : ''}`}>
                  {log.mock ? 'mock 模式' : log.model}
                </span>
                <span className="cf-log-stats">
                  {log.chars_received > 0 ? `${log.chars_received} 字 · ` : ''}
                  {log.elapsed_ms != null ? `${log.elapsed_ms}ms` : '进行中…'}
                </span>
              </div>
              {expandedId === log.call_id && (
                <div className="cf-log-detail">
                  <div className="cf-log-field">
                    <span className="cf-log-field-label">System Prompt</span>
                    <div className="cf-log-field-text">
                      {log.system_preview || '(空)'}
                    </div>
                  </div>
                  <div className="cf-log-field">
                    <span className="cf-log-field-label">User Prompt</span>
                    <div className="cf-log-field-text">
                      {log.user_preview || '(空)'}
                    </div>
                  </div>
                  {log.response_preview && (
                    <div className="cf-log-field">
                      <span className="cf-log-field-label">Response</span>
                      <div className="cf-log-field-text">
                        {log.response_preview}
                      </div>
                    </div>
                  )}
                  {log.error && (
                    <div className="cf-log-field">
                      <span className="cf-log-field-label">Error</span>
                      <div className="cf-log-field-text error">
                        {log.error}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </section>
    </div>
  )
}
