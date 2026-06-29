import { createContext, useContext, useMemo, useState, useEffect } from 'react'
import api from '../api/client'

// NOTA PRESENTACIÓN: [STATE_MANAGEMENT] Context API de React para propagar sesión y datos del usuario globalmente.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Intentamos recuperar la sesión guardada del navegador (LocalStorage)
  // para que si recarga la página F5 no tenga que volver a iniciar sesión.
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('userData') || 'null'))

  const login = async (email, password) => {
    // NOTA PRESENTACIÓN: [FASTAPI_LOGIN_OAUTH2] FastAPI requiere formato URLSearchParams (x-www-form-urlencoded) para autenticación OAuth2.
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)

    const response = await api.post('/api/auth/login', form, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const accessToken = response.data.access_token
    localStorage.setItem('token', accessToken)
    
    // Una vez dentro, pedimos nuestros datos de perfil
    const profile = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
    
    const userData = profile.data
    localStorage.setItem('userData', JSON.stringify(userData))
    
    setToken(accessToken)
    setUser(userData)
    return response.data
  }

  const register = async (email, password, nombre) => {
    const response = await api.post('/api/auth/register', { 
      email, 
      password, 
      nombre_usuario: nombre 
    })
    return response.data
  }

  const logout = () => {
    // Limpiamos todo el navegador para cerrar sesión
    localStorage.removeItem('token')
    localStorage.removeItem('userData')
    setToken(null)
    setUser(null)
  }

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
