export default function TopicView({ topic, loading, error, onStart, onRetry }) {
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>正在为你生成研究课题…</p>
      </div>
    )
  }

  if (error || !topic) {
    return (
      <section className="topic-error">
        <span className="badge">连接异常</span>
        <h2 style={{ marginTop: 18 }}>暂时无法获取课题</h2>
        <p className="muted" style={{ margin: '6px 0 4px' }}>
          {error || '未收到课题数据。请确认后端服务已启动。'}
        </p>
        <p className="muted" style={{ fontSize: '.85rem', marginBottom: 20 }}>
          后端由桌面端自动启动在随机本地端口，前端通过同源 HTTP 访问。
          若持续失败，请检查后端控制台输出或改用双脚本方案。
        </p>
        <button className="btn btn-primary" onClick={onRetry}>重新尝试</button>
      </section>
    )
  }

  return (
    <section className="topic-hero">
      <span className="badge">研究课题 · Research Topic</span>
      <h1 className="topic-q">{topic.question}</h1>

      {topic.background && (
        <div className="topic-bg">
          <span className="bg-tag">背景</span>
          <p>{topic.background}</p>
        </div>
      )}

      <button className="btn btn-primary lg" onClick={onStart}>开始研究 →</button>
      <p className="topic-hint muted">
        先思考，再查证，最后对齐主流定义。整个流程约 10–15 分钟。
      </p>
    </section>
  )
}
