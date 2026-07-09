// Backend API helpers. Base URL is configurable via VITE_API_BASE env,
// defaulting to http://localhost:8000 for local development.

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function handleError(res, fallback) {
  if (!res.ok) {
    throw new Error(`${fallback}（HTTP ${res.status}）`)
  }
}

// GET /api/topics/new?subject=<optional> -> { id, question, background }
export async function fetchNewTopic(subject) {
  const url = new URL(`${BASE}/api/topics/new`)
  if (subject) url.searchParams.set('subject', subject)
  const res = await fetch(url, {
    headers: { Accept: 'application/json' },
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
