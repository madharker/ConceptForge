import { useEffect, useState } from 'react'
import { fetchSettings, saveSettings, testConnection } from '../api'

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
    </div>
  )
}
