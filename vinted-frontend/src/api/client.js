import axios from 'axios'

const api = axios.create({
  // Usamos el proxy de Vite en desarrollo para evitar problemas de CORS y túneles
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
