import axios from 'axios'

// NOTA PRESENTACIÓN: [API_CLIENT] Cliente Axios unificado para apuntar a la URL base del backend.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// NOTA PRESENTACIÓN: [HTTP_INTERCEPTOR] Interceptor para adjuntar automáticamente el token JWT en las cabeceras de cada petición.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
