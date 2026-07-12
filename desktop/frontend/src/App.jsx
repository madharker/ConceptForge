import { useEffect, useRef, useState } from 'react'
import { fetchNewTopic, submitResearch, fetchSettings } from './api'
import TopicView from './components/TopicView'
import ResearchFlow from './components/ResearchFlow'
import ResultsView from './components/ResultsView'
import SettingsView from './components/SettingsView'

const EMPTY_RESEARCH = {
  guess: '',
  evidence: '',
  contradiction: '',
  revision: '',
  conclusion: '',
}

export default function App() {
  const [view, setView] = useState('topic') // 'topic' | 'research' | 'results' | 'settings'
  const [topic, setTopic] = useState(null)
  const [research, setResearch] = useState(EMPTY_RESEARCH)
  const [submissionId, setSubmissionId] = useState(null)

  const [loadingTopic, setLoadingTopic] = useState(true)
  const [topicError, setTopicError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  const [mockMode, setMockMode] = useState(null) // null = unknown

  // 用于取消进行中的 fetchNewTopic 请求，防止快速重试时旧响应覆盖新响应
  const topicAbortRef = useRef(null)

  useEffect(() => {
    loadTopic()
    loadSettings()
    return () => {
      // 组件卸载时取消进行中的请求
      if (topicAbortRef.current) topicAbortRef.current.abort()
    }
  }, [])

  async function loadTopic() {
    // 取消上一次进行中的请求
    if (topicAbortRef.current) topicAbortRef.current.abort()
    const controller = new AbortController()
    topicAbortRef.current = controller

    setLoadingTopic(true)
    setTopicError(null)
    try {
      const t = await fetchNewTopic(undefined, controller.signal)
      // 请求已被后续调用取消，丢弃结果
      if (controller.signal.aborted) return
      setTopic(t)
    } catch (e) {
      // AbortError 是正常的取消行为，不当作错误处理
      if (e.name === 'AbortError') return
      setTopicError(e.message || '无法连接到服务器')
    } finally {
      // 仅当这是当前活跃的请求时才结束 loading
      if (topicAbortRef.current === controller) {
        setLoadingTopic(false)
      }
    }
  }

  async function loadSettings() {
    try {
      const s = await fetchSettings()
      setMockMode(!!s.mock_mode)
    } catch (e) {
      // settings unavailable; header indicator stays hidden
    }
  }

  function startResearch() {
    setSubmitError(null)
    setView('research')
  }

  async function handleSubmit(researchData) {
    if (submitting) return // 防止提交中重复触发
    setSubmitting(true)
    setSubmitError(null)
    try {
      const res = await submitResearch({
        topic_id: topic?.id,
        ...researchData,
      })
      setSubmissionId(res.submission_id)
      setView('results')
    } catch (e) {
      setSubmitError(e.message || '提交失败，请稍后重试')
    } finally {
      setSubmitting(false)
    }
  }

  function restart() {
    setResearch(EMPTY_RESEARCH)
    setSubmissionId(null)
    setSubmitError(null)
    setView('topic')
    loadTopic()
  }

  return (
    <>
      <header className="site-header">
        <div className="hdr-inner">
          <div className="brand">
            <span className="dot" />
            <span className="cn">概念锻造器</span>
            <span className="en">ConceptForge</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {mockMode !== null && (
              <span
                className="hdr-tag"
                style={{
                  color: mockMode ? 'var(--muted)' : 'var(--accent2)',
                  border: `1px solid ${mockMode ? 'var(--rule2)' : 'var(--accent2)'}`,
                  padding: '4px 10px',
                  borderRadius: 99,
                }}
              >
                {mockMode ? 'Mock 模式' : 'LLM 已连接'}
              </span>
            )}
            <button
              className="btn btn-ghost"
              style={{ padding: '8px 16px' }}
              onClick={() => setView('settings')}
            >
              设置
            </button>
          </div>
        </div>
      </header>

      <main className="page">
        {view === 'topic' && (
          <TopicView
            topic={topic}
            loading={loadingTopic}
            error={topicError}
            onStart={startResearch}
            onRetry={loadTopic}
          />
        )}

        {view === 'research' && (
          <ResearchFlow
            topic={topic}
            research={research}
            setResearch={setResearch}
            onSubmit={handleSubmit}
            submitting={submitting}
            submitError={submitError}
          />
        )}

        {view === 'results' && (
          <ResultsView submissionId={submissionId} onRestart={restart} />
        )}

        {view === 'settings' && (
          <SettingsView onBack={() => setView('topic')} />
        )}
      </main>
    </>
  )
}
