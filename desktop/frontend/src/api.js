// Backend API helpers. Base URL is determined by the port injected by the
// desktop shell (window.__CF_PORT__, written to __port__.js by main.py).
// In Vite dev mode (no __CF_PORT__), BASE is empty so requests use a
// relative path and are proxied to the FastAPI backend via vite.config.js
// server.proxy — this avoids cross-origin issues and works when the dev
// server runs on a remote host (e.g. preview tunnel) that the browser
// can reach but 127.0.0.1:8000 cannot.

// Resolve backend port: prefer __port__.js injection; fall back to ?port= query
// (used when the bundled assets dir is read-only, e.g. installed under Program Files).
const __cfPort =
  window.__CF_PORT__ ||
  new URLSearchParams(window.location.search).get('port')

const BASE = __cfPort ? `http://127.0.0.1:${__cfPort}` : ''

function handleError(res, fallback) {
  if (!res.ok) {
    throw new Error(`${fallback}（HTTP ${res.status}）`)
  }
}

// GET /api/topics/new?subject=<optional> -> { id, question, background }
// signal: 可选 AbortSignal，用于取消请求防止竞态（旧响应覆盖新）
export async function fetchNewTopic(subject, signal) {
  // 用 URLSearchParams 拼接，避免 new URL() 在 BASE 为空时抛 Invalid URL
  const params = new URLSearchParams()
  if (subject) params.set('subject', subject)
  const qs = params.toString()
  const url = `${BASE}/api/topics/new${qs ? '?' + qs : ''}`
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
    signal,
  })
  handleError(res, '获取课题失败')
  return res.json()
}

// POST /api/submissions  body { topic_id, guess, evidence, contradiction, revision, conclusion }
// -> { submission_id }
export async function submitResearch(payload) {
  const res = await fetch(`${BASE}/api/submissions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  })
  handleError(res, '提交研究失败')
  return res.json()
}

// GET /api/submissions/{id}/evaluation -> full evaluation + alignment payload
export async function fetchEvaluation(submissionId) {
  const res = await fetch(
    `${BASE}/api/submissions/${encodeURIComponent(submissionId)}/evaluation`,
    { headers: { Accept: 'application/json' } }
  )
  handleError(res, '获取评定失败')
  return res.json()
}

// GET /api/submissions/{id}/style-summary -> { expression_style, thinking_traits, quality_overall, improvement }
export async function fetchStyleSummary(submissionId) {
  const res = await fetch(
    `${BASE}/api/submissions/${encodeURIComponent(submissionId)}/style-summary`,
    { headers: { Accept: 'application/json' } }
  )
  handleError(res, '获取风格总结失败')
  return res.json()
}

// GET /api/settings -> { base_url, api_key, model, mock_mode }
export async function fetchSettings() {
  const res = await fetch(`${BASE}/api/settings`, {
    headers: { Accept: 'application/json' },
  })
  handleError(res, '获取设置失败')
  return res.json()
}

// PUT /api/settings { base_url, api_key, model } -> { ok, mock_mode }
export async function saveSettings({ base_url, api_key, model }) {
  const res = await fetch(`${BASE}/api/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ base_url, api_key, model }),
  })
  handleError(res, '保存设置失败')
  return res.json()
}

// POST /api/settings/test { base_url, api_key, model } -> { ok, mock_mode, response } | { ok:false, error }
export async function testConnection({ base_url, api_key, model }) {
  const res = await fetch(`${BASE}/api/settings/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ base_url, api_key, model }),
  })
  handleError(res, '测试连接失败')
  return res.json()
}

// GET /api/llm/logs -> { logs: [...] }  最近 50 条 LLM 调用日志（最新在前）
export async function fetchLLMLogs() {
  const res = await fetch(`${BASE}/api/llm/logs`, {
    headers: { Accept: 'application/json' },
  })
  handleError(res, '获取 LLM 日志失败')
  return res.json()
}

// DELETE /api/llm/logs -> { ok: true }
export async function clearLLMLogs() {
  const res = await fetch(`${BASE}/api/llm/logs`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  })
  handleError(res, '清空日志失败')
  return res.json()
}
