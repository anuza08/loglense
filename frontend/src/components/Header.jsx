import styles from './Header.module.css'

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <span className={styles.logo}>🔍 LogLense</span>
        <span className={styles.subtitle}>LLM-powered CI/CD Analyzer</span>
      </div>
      {/* <span className={styles.badge}>Claude AI</span> */}
    </header>
  )
}
