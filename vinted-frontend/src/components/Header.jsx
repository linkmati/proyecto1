import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useEffect, useState } from 'react'
import api from '../api/client'

export default function Header() {
  const { isAuthenticated, logout, userEmail } = useAuth()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    if (!isAuthenticated) return

    const fetchUnread = async () => {
      try {
        const res = await api.get('/api/mensajes/no-leidos/conteo')
        setUnreadCount(res.data.count || 0)
      } catch (err) {
        console.error('Error fetching unread count:', err)
      }
    }

    fetchUnread()
    const interval = setInterval(fetchUnread, 15000) // Polling cada 15s
    return () => clearInterval(interval)
  }, [isAuthenticated])

  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link to="/" className="brand">
          <span className="brand__logo">MT</span>
          <div>
            <strong>Mas Tienda</strong>
            <small>Moda, gadgets y oportunidades con estilo</small>
          </div>
        </Link>

        <nav className="nav">
          <NavLink to="/">Inicio</NavLink>
          <NavLink to="/publicar">Publicar</NavLink>
          {isAuthenticated && (
            <NavLink to="/mensajes" style={{ position: 'relative' }}>
              Mensajes
              {unreadCount > 0 && (
                <span style={{
                  position: 'absolute',
                  top: '-5px',
                  right: '-10px',
                  background: '#ef4444',
                  color: 'white',
                  borderRadius: '50%',
                  width: '18px',
                  height: '18px',
                  fontSize: '0.7rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '2px solid white'
                }}>
                  {unreadCount}
                </span>
              )}
            </NavLink>
          )}
          {!isAuthenticated && <NavLink to="/auth">Entrar</NavLink>}
        </nav>

        <div className="header-actions">
          {isAuthenticated ? (
            <>
              <Link to="/perfil" className="pill">{userEmail || 'Mi perfil'}</Link>
              <button className="button button--ghost" onClick={logout}>
                Salir
              </button>
            </>
          ) : (
            <Link className="button button--primary" to="/auth">
              Acceder
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
