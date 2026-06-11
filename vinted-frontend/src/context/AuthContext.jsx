import { createContext, useContext, useMemo, useState, useEffect } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Intentamos recuperar la sesión guardada del navegador al arrancar la app
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('userData') || 'null'))

  const login = async (email, password) => {
    // Para entrar, mandamos los datos en formato de formulario (lo que pide FastAPI)
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)

    const response = await api.post('/api/auth/login', form, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const accessToken = response.data.access_token
    // Guardamos el token para no tener que loguearnos cada vez que refresquemos la página
    localStorage.setItem('token', accessToken)
    
    // Una vez dentro, pedimos nuestros datos de perfil para saber el nombre y el rol
    const profile = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
    
    const userData = profile.data
    console.log("DEBUG - AuthContext: Logged in user data:", userData)
    
    localStorage.setItem('userData', JSON.stringify(userData))
    
    setToken(accessToken)
    setUser(userData)
    return response.data
  }

  const register = async (email, password, nombre) => {
    // Mandamos los datos básicos para crear una cuenta nueva
    const response = await api.post('/api/auth/register', { 
      email, 
      password, 
      nombre_usuario: nombre 
    })
    return response.data
  }

  const logout = () => {
    // Para salir, simplemente borramos todo lo que guardamos en el navegador
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
