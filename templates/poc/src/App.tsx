/**
 * PoC shell — REPLACE the placeholder view with the project's screens.
 * Keep: demo badge, MZtech branding, sidebar layout, mock-data wiring.
 */
import { useState } from 'react'
import './styles.css'

const NAV = [
  { id: 'view1', label: 'Vista principal' },
  { id: 'view2', label: 'Segunda vista' },
]

export default function App() {
  // Deep-linkable views: #view2 opens the second screen (handy for proposal links)
  const [view, setView] = useState(() => {
    const h = window.location.hash.replace('#', '')
    return NAV.some((n) => n.id === h) ? h : 'view1'
  })

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <img src="/favicon.svg" alt="MZtech" />
          <div className="name">MZ<span>tech</span> · PoC</div>
        </div>
        <div className="section">Navegación</div>
        {NAV.map((n) => (
          <button
            key={n.id}
            className={`nav-item ${view === n.id ? 'active' : ''}`}
            onClick={() => setView(n.id)}
          >
            {n.label}
          </button>
        ))}
        <div className="foot">Demo con datos ficticios.<br />Sin backend ni usuarios reales.</div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div>
            <h1>Nombre del PoC</h1>
            <div className="sub">Prototipo funcional · MZtech</div>
          </div>
          <div className="spacer" />
          <span className="demo-badge">Demo · datos ficticios</span>
        </header>

        <main className="content">
          <div className="card">
            <h2>{view === 'view1' ? 'Vista principal' : 'Segunda vista'}</h2>
            <p className="muted">
              Sustituye este shell por las pantallas del PoC: datos desde
              <code> src/data/fixtures.ts</code>, persistencia con
              <code> src/lib/mock.ts</code> (localStorage + latencia simulada).
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}
