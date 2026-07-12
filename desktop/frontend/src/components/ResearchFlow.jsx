import { useState } from 'react'

// The 5-step research flow. Step labels + guidance prompts rendered verbatim
// from the approved spec (Task 7, SubTask 7.1).
const STEPS = [
  {
    key: 'guess',
    label: '原始猜想',
    prompt: '在查任何资料之前，你对这个课题的第一直觉是什么？',
  },
  {
    key: 'evidence',
    label: '收集证据',
    prompt: '你找到了哪些信息来支持或推翻你的猜想？',
  },
  {
    key: 'contradiction',
    label: '遇到矛盾',
    prompt: '有没有哪些证据和你的猜想不一致？你怎么处理？',
  },
  {
    key: 'revision',
    label: '修正理解',
    prompt: '根据新证据，你修改了哪些想法？',
  },
  {
    key: 'conclusion',
    label: '临时结论',
    prompt: '用你自己的话，给出当前对这个问题最完整的解释。',
  },
]

export default function ResearchFlow({
  topic,
  research,
  setResearch,
  onSubmit,
  submitting,
  submitError,
}) {
  const [idx, setIdx] = useState(0)
  const [localError, setLocalError] = useState(null)
  const step = STEPS[idx]
  const isFirst = idx === 0
  const isLast = idx === STEPS.length - 1

  function update(val) {
    setResearch((prev) => ({ ...prev, [step.key]: val }))
    if (localError) setLocalError(null)
  }

  function next() {
    // 校验当前步骤非空
    if (!String(research[step.key] || '').trim()) {
      setLocalError(`请先完成「${step.label}」再进入下一步`)
      return
    }
    setLocalError(null)
    setIdx((i) => Math.min(STEPS.length - 1, i + 1))
  }

  function prev() {
    setLocalError(null)
    setIdx((i) => Math.max(0, i - 1))
  }

  function handleSubmit() {
    // 提交前校验全部 5 个字段非空
    const empty = STEPS.find((s) => !String(research[s.key] || '').trim())
    if (empty) {
      setLocalError(`「${empty.label}」还未填写，请补全后再提交`)
      setIdx(STEPS.findIndex((s) => s.key === empty.key))
      return
    }
    setLocalError(null)
    onSubmit(research)
  }

  return (
    <div className="research-flow">
      <div className="topic-recap">
        <span className="recap-label">研究课题</span>
        <p className="recap-q">{topic?.question}</p>
      </div>

      <ol className="stepper" aria-label="研究步骤">
        {STEPS.map((s, i) => {
          const cls = ['step']
          if (i === idx) cls.push('active')
          if (i < idx) cls.push('done')
          // 标记已填写的步骤
          if (String(research[s.key] || '').trim() && i !== idx) cls.push('filled')
          return (
            <li key={s.key} className={cls.join(' ')}>
              <span className="step-num">{String(i + 1).padStart(2, '0')}</span>
              <span className="step-label">{s.label}</span>
            </li>
          )
        })}
      </ol>

      <section className="step-panel" key={step.key}>
        <div className="step-meta">
          <span className="step-tag">
            第 {idx + 1} 步 / 共 {STEPS.length} 步
          </span>
          <span className="step-name">{step.label}</span>
        </div>

        <h2 className="step-prompt">{step.prompt}</h2>

        <textarea
          className="step-textarea"
          value={research[step.key] || ''}
          onChange={(e) => update(e.target.value)}
          placeholder="在此写下你的思考…"
          rows={10}
          autoFocus
        />

        {(localError || submitError) && (
          <div className="error-box">{localError || submitError}</div>
        )}

        <div className="step-nav">
          <button
            className="btn btn-ghost"
            onClick={prev}
            disabled={isFirst || submitting}
          >
            ← 上一步
          </button>

          {isLast ? (
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? '提交中…' : '提交研究'}
            </button>
          ) : (
            <button className="btn btn-primary" onClick={next}>
              下一步 →
            </button>
          )}
        </div>
      </section>
    </div>
  )
}
