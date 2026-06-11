import axios from 'axios'

// Configuramos Axios para no tener que escribir la URL entera cada vez que llamamos a la API
const api = axios.create({
  // Usamos el proxy de Vite en desarrollo para evitar problemas de CORS y túneles
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Este interceptor se ejecuta ANTES de cada petición a la API
api.interceptors.request.use((config) => {
  // Si tenemos un token guardado en el navegador, lo metemos en la cabecera
  // Así el servidor sabe quiénes somos
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
