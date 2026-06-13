import { createContext, useContext, useMemo, useState, useEffect } from 'react'
import api from '../api/client'

// NOTA PRESENTACIÓN: Usamos el Context API de React para manejar el estado global.
// Esto nos permite acceder a los datos del usuario (token, nombre, si está logueado)
// desde cualquier componente de la aplicación, sin tener que ir pasando 'props' de un componente a otro.
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // Intentamos recuperar la sesión guardada del navegador (LocalStorage)
  // para que si recarga la página F5 no tenga que volver a iniciar sesión.
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('userData') || 'null'))

  const login = async (email, password) => {
    // NOTA PRESENTACIÓN: FastAPI requiere que los datos del login vayan como un formulario tradicional 
    // (x-www-form-urlencoded) en lugar de un JSON normal, por eso usamos URLSearchParams.
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
