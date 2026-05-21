import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Toast from '../components/Toast'

export default function AuthPage() {
  const [searchParams] = useSearchParams()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [nombre, setNombre] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const { login, register } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const mode = searchParams.get('mode')
    if (mode === 'register') {
      setIsLogin(false)
    } else {
      setIsLogin(true)
    }
  }, [searchParams])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (isLogin) {
        await login(email, password)
      } else {
        await register(email, password, nombre)
      }
      navigate('/')
    } catch (error) {
      setToast({ 
        message: error.response?.data?.detail || 'Error en la autenticación', 
        tone: 'error' 
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container" style={{ display: 'grid', placeItems: 'center', minHeight: 'calc(100vh - var(--header-height))' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px', padding: '40px' }}>
        <h1 style={{ textAlign: 'center', marginBottom: '8px' }}>
          {isLogin ? '¡Hola de nuevo!' : 'Crea tu cuenta'}
        </h1>
        <p style={{ textAlign: 'center', color: 'var(--text-soft)', marginBottom: '32px', fontSize: '0.9rem' }}>
          {isLogin ? 'Introduce tus datos para acceder' : 'Únete a la mayor comunidad de segunda mano'}
        </p>

        <form className="form" onSubmit={handleSubmit}>
          {!isLogin && (
            <div>
              <label>Nombre de usuario</label>
              <input
                type="text"
                required
                className="search-input"
                style={{ paddingLeft: '16px' }}
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
          )}
          <div>
            <label>Email</label>
            <input
              type="email"
              required
              className="search-input"
              style={{ paddingLeft: '16px' }}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label>Contraseña</label>
            <input
              type="password"
              required
              className="search-input"
              style={{ paddingLeft: '16px' }}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', marginTop: '12px', padding: '14px', borderRadius: '4px' }}
            disabled={loading}
          >
            {loading ? 'Cargando...' : isLogin ? 'Iniciar sesión' : 'Registrarse'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>
            {isLogin ? '¿No tienes cuenta? ' : '¿Ya tienes cuenta? '}
          </span>
          <button 
            className="btn btn-ghost" 
            style={{ padding: '4px 8px', color: 'var(--primary)', fontWeight: '700' }}
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? 'Regístrate' : 'Inicia sesión'}
          </button>
        </div>
      </div>

      <Toast
        message={toast.message}
        tone={toast.tone}
        onClose={() => setToast({ message: '', tone: 'success' })}
      />
    </div>
  )
}
