import axios from 'axios'

// NOTA PRESENTACIÓN: Configuramos Axios (la librería para hacer peticiones al backend)
// para tener un punto centralizado. En desarrollo tira de localhost, en pro tira de la URL de Render.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// NOTA PRESENTACIÓN: Esto es un Interceptor. 
// Funciona como un "guardia de seguridad" que revisa todas las peticiones ANTES de que salgan 
// hacia el servidor. Si el usuario ha iniciado sesión (tiene token guardado en el navegador),
// el interceptor inyecta automáticamente la cabecera 'Authorization: Bearer <token>' 
// en cada petición, así no tenemos que escribir ese código en cada pantalla de la web.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
