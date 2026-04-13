import styles from './AnalysisPanel.module.css'

const RESULT_CLASS = {
  SUCCESS: styles.success,
  FAILURE: styles.failure,
  UNSTABLE: styles.warning,
  IN_PROGRESS: styles.inprogress,
}

function ResultBadge({ result }) {
  return (
    <span className={`${styles.badge} ${RESULT_CLASS[result] || styles.inprogress}`}>
      {result}
    </span>
  )
}

function MetaGrid({ items }) {
  return (
    <div className={styles.metaGrid}>
      {items.map(({ label, value }) => (
        <div key={label} className={styles.metaItem}>
          <span className={styles.metaLabel}>{label}</span>
          <span className={styles.metaValue}>{value || '—'}</span>
        </div>
      ))}
    </div>
  )
}

function renderMd(text) {
  return text
    .replace(/### (.+)/g, '<h3 class="md-h3">$1</h3>')
    .replace(/## (.+)/g, '<h3 class="md-h3">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="md-code">$1</code>')
}

function durationStr(ms) {
  if (!ms) return '—'
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  return m ? `${m}m ${s % 60}s` : `${s}s`
}

export default function AnalysisPanel({ state }) {
  const { loading, error, data, type } = state

  if (loading) {
    return (
      <div className={styles.centered}>
        <div className={styles.spinner} />
        <span className={styles.loadingText}>
          {type === 'analyse' ? 'Running full LLM analysis…' :
           type === 'quick'   ? 'Generating quick summary…' :
           type === 'trend'   ? 'Analyzing build trend…' :
                                'Fetching build info…'}
        </span>
      </div>
    )
  }

  if (error) {
    return <div className={styles.errorBox}><b>Error:</b> {error}</div>
  }

  if (!data) {
    return (
      <div className={styles.placeholder}>
        <h2>Welcome to LogLense</h2>
        <p>Enter a Jenkins job name and click an action to analyze builds.</p>
        <p>Or refresh the Jobs list in the sidebar to browse available jobs.</p>
      </div>
    )
  }

  // Build Info
  if (type === 'meta') {
    return (
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>{data.job_name}</span>
          <ResultBadge result={data.result} />
        </div>
        <MetaGrid items={[
          { label: 'Build', value: `#${data.build_number}` },
          { label: 'Duration', value: durationStr(data.duration_ms) },
          { label: 'Triggered by', value: data.causes?.join(', ') },
          { label: 'Culprits', value: data.culprits?.join(', ') },
        ]} />
        {data.url && (
          <a href={data.url} target="_blank" rel="noreferrer" className={styles.link}>
            Open in Jenkins ↗
          </a>
        )}
      </div>
    )
  }

  // Full Analysis
  if (type === 'analyse') {
    return (
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Failure Analysis — {data.job_name} #{data.build_number}</span>
          <ResultBadge result={data.result} />
        </div>
        <div
          className={styles.analysisBody}
          dangerouslySetInnerHTML={{ __html: renderMd(data.analysis) }}
        />
        <div className={styles.tokenInfo}>
          <span>Prompt tokens: <b>{data.prompt_tokens}</b></span>
          <span>Completion tokens: <b>{data.completion_tokens}</b></span>
          <span>Cached tokens: <b>{data.cached_tokens}</b></span>
        </div>
      </div>
    )
  }

  // Quick Summary
  if (type === 'quick') {
    return (
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Quick Summary — {data.job_name} #{data.build_number}</span>
          <ResultBadge result={data.result} />
        </div>
        <div
          className={styles.analysisBody}
          dangerouslySetInnerHTML={{ __html: renderMd(data.summary) }}
        />
      </div>
    )
  }

  // Trend
  if (type === 'trend') {
    return (
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Build Trend — {data.job_name}</span>
        </div>
        <div
          className={styles.analysisBody}
          dangerouslySetInnerHTML={{ __html: renderMd(data.analysis) }}
        />
      </div>
    )
  }

  return null
}
