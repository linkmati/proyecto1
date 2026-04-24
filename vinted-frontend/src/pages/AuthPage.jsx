import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'

export default function AuthPage() {
  const navigate = useNavigate()
  const { login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ email: '', password: '' })
  const [toast, setToast] = useState({ message: '', tone: 'success' })
  const [loading, setLoading] = useState(false)

  const onChange = (e) => {
    setForm((current) => ({ ...current, [e.target.name]: e.target.value }))
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      if (mode === 'register') {
        await register(form)
        setToast({
          message: 'Cuenta creada. Ahora inicia sesión para publicar y ofertar.',
          tone: 'success',
        })
        setMode('login')
      } else {
        await login(form)
        navigate('/')
      }
    } catch (error) {
      setToast({
        message: error.response?.data?.detail || 'No se pudo completar la operación.',
        tone: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="container auth-layout">
      <div className="auth-copy card">
        <span className="eyebrow">Acceso seguro</span>
        <h1>{mode === 'login' ? 'Bienvenido de nuevo' : 'Crea tu cuenta'}</h1>
        <p>
          Tu backend usa Supabase Auth. Aquí ya está preparado el formulario para
          registrarse e iniciar sesión sin pelearte con tokens a mano.
        </p>
        <ul className="feature-list">
          <li>Login con JWT</li>
          <li>Persistencia de sesión en localStorage</li>
          <li>Preparado para publicar artículos y mandar ofertas</li>
        </ul>
      </div>

      <div className="card auth-form-card">
        <div className="tab-row">
          <button
            className={mode === 'login' ? 'tab tab--active' : 'tab'}
            onClick={() => setMode('login')}
            type="button"
          >
            Iniciar sesión
          </button>
          <button
            className={mode === 'register' ? 'tab tab--active' : 'tab'}
            onClick={() => setMode('register')}
            type="button"
          >
            Registrarse
          </button>
        </div>

        <form className="form" onSubmit={onSubmit}>
          <label>
            Correo electrónico
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={onChange}
              required
              placeholder="ejemplo@correo.com"
            />
          </label>

          <label>
            Contraseña
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={onChange}
              required
              placeholder="Tu contraseña"
            />
          </label>

          <button className="button button--primary button--full" disabled={loading}>
            {loading
              ? 'Procesando...'
              : mode === 'login'
                ? 'Entrar'
                : 'Crear cuenta'}
          </button>
        </form>
      </div>

      <Toast
        message={toast.message}
        tone={toast.tone}
        onClose={() => setToast({ message: '', tone: 'success' })}
      />
    </section>
  )
}
