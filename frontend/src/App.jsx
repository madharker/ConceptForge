import { useEffect, useState } from 'react'
import { fetchNewTopic, submitResearch } from './api'
import TopicView from './components/TopicView'
import ResearchFlow from './components/ResearchFlow'
import ResultsView from './components/ResultsView'

const EMPTY_RESEARCH = {
  guess: '',
  evidence: '',
  contradiction: '',
  revision: '',
  conclusion: '',
}

export default function App() {
  const [view, setView] = useState('topic') // 'topic' | 'research' | 'results'
  const [topic, setTopic] = useState(null)
  const [research, setResearch] = useState(EMPTY_RESEARCH)
  const [submissionId, setSubmissionId] = useState(null)

  const [loadingTopic, setLoadingTopic] = useState(true)
  const [topicError, setTopicError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  useEffect(() => {
    loadTopic()
  }, [])

  async function loadTopic() {
    setLoadingTopic(true)
    setTopicError(null)
    try {
      const t = await fetchNewTopic()
      setTopic(t)
    } catch (e) {
      setTopicError(e.message || '无法连接到服务器')
    } finally {
      setLoadingTopic(false)
    }
  }

  function startResearch() {
    setSubmitError(null)
    setView('research')
  }

  async function handleSubmit(researchData) {
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
          <span className="hdr-tag">先研究 · 后定义</span>
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
      </main>
    </>
  )
}
