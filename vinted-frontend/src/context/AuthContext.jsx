import { createContext, useContext, useMemo, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail') || '')
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '')
  const [role, setRole] = useState(localStorage.getItem('role') || 'user')

  const login = async ({ email, password }) => {
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
    localStorage.setItem('userEmail', email)
    
    // Fetch UUID and Role
    const profile = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
    
    localStorage.setItem('userId', profile.data.id_usuario)
    localStorage.setItem('role', profile.data.rol)
    setToken(accessToken)
    setUserEmail(email)
    setUserId(profile.data.id_usuario)
    setRole(profile.data.rol)
    return response.data
  }

  const register = async ({ email, password }) => {
    const response = await api.post('/api/auth/register', { email, password })
    return response.data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userId')
    localStorage.removeItem('role')
    setToken(null)
    setUserEmail('')
    setUserId('')
    setRole('user')
  }

  const value = useMemo(
    () => ({
      token,
      userId,
      role,
      isAuthenticated: Boolean(token),
      userEmail,
      login,
      register,
      logout,
    }),
    [token, userEmail, userId, role],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
