import axios from 'axios'

const api = axios.create({
  // Si estamos en el navegador, usamos la IP desde la que accedemos a la web para el backend
  baseURL: import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`,
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
