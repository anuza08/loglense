import { useState } from 'react'
import styles from './JobList.module.css'

export default function JobList({ onSelect }) {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function fetchJobs() {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/v1/jobs')
      if (!res.ok) throw new Error(await res.text())
      setJobs(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function healthColor(score) {
    if (score >= 80) return 'var(--success)'
    if (score >= 50) return 'var(--warning)'
    return 'var(--failure)'
  }

  return (
    <div className={styles.container}>
      <div className={styles.titleRow}>
        <span className={styles.title}>Jenkins Jobs</span>
        <button className={styles.refreshBtn} onClick={fetchJobs} disabled={loading}>
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {!jobs.length && !error && (
        <p className={styles.hint}>Click Refresh to load jobs</p>
      )}

      <div className={styles.list}>
        {jobs.map(job => (
          <div key={job.name} className={styles.jobCard} onClick={() => onSelect(job.name)}>
            <div className={styles.jobName}>{job.name}</div>
            <div className={styles.jobMeta}>
              Last build: #{job.last_build_number ?? '—'} &nbsp;|&nbsp; Health: {job.health_score}%
            </div>
            <div className={styles.healthBar}>
              <div
                className={styles.healthFill}
                style={{ width: `${job.health_score}%`, background: healthColor(job.health_score) }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
