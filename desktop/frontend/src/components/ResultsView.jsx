import { useEffect, useState } from 'react'
import { fetchEvaluation, fetchStyleSummary } from '../api'

// Map the backend's english dimension keys to readable Chinese labels,
// in the fixed display order from the spec.
const DIMENSIONS = [
  { key: 'problem_understanding', label: '问题理解' },
  { key: 'evidence_quality', label: '证据质量' },
  { key: 'reasoning_chain', label: '推理链条' },
  { key: 'concept_boundary', label: '概念边界' },
  { key: 'contradiction_handling', label: '矛盾处理' },
]

const LAYERS = [
  { key: 'your_expression', label: '你的表达' },
  { key: 'rigorous_rewrite', label: '严谨改写' },
  { key: 'mainstream_definition', label: '主流定义' },
]

const DIFFS = [
  { key: 'got_right', label: '你说对了什么' },
  { key: 'missed', label: '你漏掉了什么' },
  { key: 'gap', label: '你和主流定义差在哪里' },
  { key: 'why_limited', label: '为什么主流定义要这样限定' },
]

const STYLE_FIELDS = [
  { key: 'expression_style', label: '表达风格' },
  { key: 'thinking_traits', label: '思维特征' },
  { key: 'quality_overall', label: '质量总评' },
  { key: 'improvement', label: '改进建议' },
]

export default function ResultsView({ submissionId, onRestart }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [styleSummary, setStyleSummary] = useState(null)
  const [styleLoading, setStyleLoading] = useState(false)
  const [styleError, setStyleError] = useState(null)
  const [styleExpanded, setStyleExpanded] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    fetchEvaluation(submissionId)
      .then((d) => {
        if (alive) setData(d)
      })
      .catch((e) => {
        if (alive) setError(e.message || '获取评定失败')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [submissionId])

  // On-demand fetch for the style summary. Triggered only when the user
  // clicks the "查看风格与质量总结" button, so a slow/failed summary fetch
  // never blocks the main evaluation modules.
  const loadStyleSummary = () => {
    setStyleLoading(true)
    setStyleError(null)
    fetchStyleSummary(submissionId)
      .then((d) => setStyleSummary(d))
      .catch((e) => setStyleError(e.message || '获取风格总结失败'))
      .finally(() => setStyleLoading(false))
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>正在生成评定与对齐…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-box big">
        <div>
          <strong>获取评定失败</strong>
          <div className="muted" style={{ marginTop: 4 }}>{error}</div>
        </div>
        <button className="btn btn-primary" onClick={onRestart}>换一个课题</button>
      </div>
    )
  }

  const evaluation = data?.evaluation || {}
  const alignment = data?.alignment || { layers: {}, diff: {} }
  const layers = alignment.layers || {}
  const diff = alignment.diff || {}
  const topic = data?.topic || {}

  return (
    <div className="results">
      <header className="results-header">
        <span className="badge">评定与对齐 · Evaluation</span>
        <h2>{topic.question || '研究完成'}</h2>
      </header>

      {/* 五维评定 */}
      <section className="module">
        <h3 className="module-title">五维评定</h3>
        <ul className="dim-list">
          {DIMENSIONS.map(({ key, label }) => {
            const d = evaluation[key] || {}
            return (
              <li key={key} className="dim-item">
                <div className="dim-head">
                  <span className="dim-label">{label}</span>
                  {d.verdict && <span className="verdict">{d.verdict}</span>}
                </div>
                {d.detail && <p className="dim-detail">{d.detail}</p>}
              </li>
            )
          })}
        </ul>
      </section>

      {/* 三层表述 */}
      <section className="module">
        <h3 className="module-title">三层表述</h3>
        <div className="layer-stack">
          {LAYERS.map(({ key, label }) => (
            <article key={key} className="layer-card">
              <span className="layer-tag">{label}</span>
              <p className="layer-text">{layers[key] || '—'}</p>
            </article>
          ))}
        </div>
      </section>

      {/* 差异说明 */}
      <section className="module">
        <h3 className="module-title">差异说明</h3>
        <ul className="diff-list">
          {DIFFS.map(({ key, label }) => (
            <li key={key} className="diff-item">
              <span className="diff-label">{label}</span>
              <p className="diff-text">{diff[key] || '—'}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* 风格与质量总结 */}
      <section className="module">
        <h3 className="module-title">风格与质量总结</h3>
        {!styleExpanded && (
          <button
            className="btn btn-primary"
            onClick={() => {
              setStyleExpanded(true)
              if (!styleSummary) loadStyleSummary()
            }}
          >
            {styleSummary ? '展开风格与质量总结' : '查看风格与质量总结'}
          </button>
        )}
        {styleExpanded && styleLoading && (
          <p className="module-note">正在生成风格总结…</p>
        )}
        {styleExpanded && styleError && (
          <div>
            <p className="module-note">{styleError}</p>
            <button className="btn btn-primary" onClick={loadStyleSummary}>重试</button>
          </div>
        )}
        {styleExpanded && styleSummary && !styleLoading && (
          <>
            <ul className="diff-list">
              {STYLE_FIELDS.map(({ key, label }) => (
                <li key={key} className="diff-item">
                  <span className="diff-label">{label}</span>
                  <p className="diff-text">{styleSummary?.[key] || '—'}</p>
                </li>
              ))}
            </ul>
            <div className="results-actions" style={{ marginTop: 12, paddingTop: 0, borderTop: 'none' }}>
              <button className="btn btn-ghost" onClick={() => setStyleExpanded(false)}>
                收起风格总结
              </button>
            </div>
          </>
        )}
      </section>

      <div className="results-actions">
        <button className="btn btn-primary lg" onClick={onRestart}>
          换一个课题 →
        </button>
      </div>
    </div>
  )
}
