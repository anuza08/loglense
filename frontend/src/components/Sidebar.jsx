import { useState } from 'react'
import JobList from './JobList'
import styles from './Sidebar.module.css'

export default function Sidebar({ onAction }) {
  const [job, setJob] = useState('')
  const [build, setBuild] = useState('')

  function trigger(action) {
    if (!job.trim()) return alert('Enter a job name first.')
    onAction({ action, job: job.trim(), build: build.trim() || 'lastBuild' })
  }

  return (
    <aside className={styles.sidebar}>
      <div>
        <p className={styles.sectionTitle}>Jenkins Connection</p>

        <div className={styles.formGroup}>
          <label className={styles.label}>Job Name</label>
          <input
            className={styles.input}
            type="text"
            placeholder="e.g. test-failure-job"
            value={job}
            onChange={e => setJob(e.target.value)}
          />
        </div>

        <div className={styles.formGroup} style={{ marginTop: 10 }}>
          <label className={styles.label}>Build Number</label>
          <input
            className={styles.input}
            type="text"
            placeholder="lastBuild (default)"
            value={build}
            onChange={e => setBuild(e.target.value)}
          />
        </div>
      </div>

      <div className={styles.actionGrid}>
        <button className={`${styles.btn} ${styles.primary}`} onClick={() => trigger('analyse')}>
          Full Analysis
        </button>
        <button className={`${styles.btn} ${styles.secondary}`} onClick={() => trigger('quick')}>
          Quick Summary
        </button>
        <button className={`${styles.btn} ${styles.secondary}`} onClick={() => trigger('meta')}>
          Build Info
        </button>
        <button className={`${styles.btn} ${styles.secondary}`} onClick={() => trigger('trend')}>
          Trend
        </button>
      </div>

      <hr className={styles.divider} />

      <JobList onSelect={name => setJob(name)} />
    </aside>
  )
}
