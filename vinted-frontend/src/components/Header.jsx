import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Header() {
  const { isAuthenticated, logout, userEmail } = useAuth()

  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link to="/" className="brand">
          <span className="brand__logo">LM</span>
          <div>
            <strong>Linkmati Market</strong>
            <small>Moda, gadgets y oportunidades con estilo</small>
          </div>
        </Link>

        <nav className="nav">
          <NavLink to="/">Inicio</NavLink>
          <NavLink to="/publicar">Publicar</NavLink>
          <NavLink to="/negociar">Negociar</NavLink>
          {isAuthenticated && <NavLink to="/mensajes">Mensajes</NavLink>}
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
