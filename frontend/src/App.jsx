import { useState } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import AnalysisPanel from './components/AnalysisPanel'
import styles from './App.module.css'

const API = '/api/v1'

export default function App() {
  const [panelState, setPanelState] = useState({
    loading: false,
    error: '',
    data: null,
    type: null,
  })

  async function handleAction({ action, job, build }) {
    setPanelState({ loading: true, error: '', data: null, type: action })

    try {
      let res, data

      if (action === 'meta') {
        res = await fetch(`${API}/jobs/${encodeURIComponent(job)}/builds/${build}`)
        if (!res.ok) throw new Error(await res.text())
        data = await res.json()
      } else if (action === 'analyse') {
        res = await fetch(`${API}/jobs/${encodeURIComponent(job)}/builds/${build}/analyse`)
        if (!res.ok) throw new Error(await res.text())
        data = await res.json()
      } else if (action === 'quick') {
        res = await fetch(`${API}/jobs/${encodeURIComponent(job)}/builds/${build}/quick-summary`)
        if (!res.ok) throw new Error(await res.text())
        data = await res.json()
      } else if (action === 'trend') {
        res = await fetch(`${API}/jobs/${encodeURIComponent(job)}/trend`)
        if (!res.ok) throw new Error(await res.text())
        data = await res.json()
      }

      setPanelState({ loading: false, error: '', data, type: action })
    } catch (e) {
      let msg = e.message
      try { msg = JSON.parse(msg).detail ?? msg } catch {}
      setPanelState({ loading: false, error: msg, data: null, type: action })
    }
  }

  return (
    <div className={styles.app}>
      <Header />
      <div className={styles.body}>
        <Sidebar onAction={handleAction} />
        <main className={styles.main}>
          <AnalysisPanel state={panelState} />
        </main>
      </div>
    </div>
  )
}
