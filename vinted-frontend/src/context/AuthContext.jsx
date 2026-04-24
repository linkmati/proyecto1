import { createContext, useContext, useMemo, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail') || '')
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '')

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
    
    // Fetch UUID
    const profile = await api.get('/api/users/me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    })
    
    localStorage.setItem('userId', profile.data.id_usuario)
    setToken(accessToken)
    setUserEmail(email)
    setUserId(profile.data.id_usuario)
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
    setToken(null)
    setUserEmail('')
    setUserId('')
  }

  const value = useMemo(
    () => ({
      token,
      userId,
      isAuthenticated: Boolean(token),
      userEmail,
      login,
      register,
      logout,
    }),
    [token, userEmail, userId],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
