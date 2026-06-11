import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import ArticleCard from '../components/ArticleCard'
import Hero from '../components/Hero'
import Toast from '../components/Toast'
import OfferModal from '../components/OfferModal'
import { motion, AnimatePresence } from 'framer-motion'

export default function HomePage({ searchTerm = '' }) {
  const { isAuthenticated } = useAuth()
  const [articles, setArticles] = useState([])
  const [favorites, setFavorites] = useState([])
  const [category, setCategory] = useState('Todas')
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const CATEGORIAS = ['Todas', 'Moda', 'Hogar', 'Electrónica', 'Entretenimiento', 'Otros']

  // Esta función es la que pide los datos al servidor
  const loadData = async () => {
    try {
      setLoading(true)
      const params = { limit: 20 }
      // Si el usuario ha elegido una categoría, la añadimos a la consulta
      if (category !== 'Todas') params.categoria = category
      // Si hay algo escrito en el buscador, también lo filtramos
      if (searchTerm.trim()) params.search = searchTerm.trim()
      
      // Pedimos los artículos y los favoritos a la vez para ir más rápido
      const [artRes, favRes] = await Promise.all([
        api.get('/api/items', { params }).catch(() => ({ data: [] })),
        isAuthenticated ? api.get('/api/favorites').catch(() => ({ data: [] })) : Promise.resolve({ data: [] })
      ])
      
      setArticles(Array.isArray(artRes.data) ? artRes.data : [])
      // Guardamos solo los IDs de los favoritos para saber qué corazones pintar de rojo
      const favIds = (Array.isArray(favRes.data) ? favRes.data : []).map(f => String(f.id_articulo))
      setFavorites(favIds)
    } catch (error) {
      console.error('Error general en loadData:', error)
      setToast({ message: 'Error de conexión con el servidor.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // Cada vez que cambie la búsqueda o la categoría, volvemos a cargar los datos
  useEffect(() => {
    // Ponemos un pequeño retraso para no agobiar al servidor si el usuario escribe muy rápido
    const timer = setTimeout(() => {
      loadData()
    }, 400)
    return () => clearTimeout(timer)
  }, [searchTerm, category, isAuthenticated])

  // Para marcar o desmarcar como favorito
  const toggleFavorite = async (id) => {
    if (!isAuthenticated) {
      setToast({ message: 'Inicia sesión para guardar favoritos.', tone: 'error' })
      return
    }

    const idStr = String(id)
    const isFav = favorites.includes(idStr)

    try {
      if (isFav) {
        setFavorites(prev => prev.filter(f => f !== idStr))
        await api.delete(`/api/favorites/${id}`)
      } else {
        setFavorites(prev => [...prev, idStr])
        await api.post(`/api/favorites/${id}`) // FIXED ENDPOINT
      }
    } catch (e) {
      console.error('Toggle favorite error:', e)
      loadData()
      setToast({ message: 'Error al actualizar favoritos.', tone: 'error' })
    }
  }

  return (
    <div style={{ background: 'var(--bg)' }}>
      <Hero />

      <div className="container" id="items-grid">
        <div style={{ marginBottom: '32px' }}>
           <h2 style={{ fontSize: '1.5rem', marginBottom: '20px', fontWeight: '600' }}>
             {searchTerm ? `Resultados para "${searchTerm}"` : (category === 'Todas' ? 'Novedades' : category)}
           </h2>
           
           <div className="cat-bar">
             {CATEGORIAS.map(cat => (
               <button 
                 key={cat} 
                 className={`cat-item ${category === cat ? 'active' : ''}`}
                 onClick={() => setCategory(cat)}
               >
                 {cat}
               </button>
             ))}
           </div>
        </div>

        {loading ? (
          <div className="article-grid">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="article-card" style={{ height: '300px', background: 'var(--surface-muted)', borderRadius: 'var(--radius-sm)' }} />
            ))}
          </div>
        ) : (
          <div className="article-grid">
            {articles.length === 0 ? (
              <div className="empty-state" style={{ padding: '60px 0', textAlign: 'center', gridColumn: '1/-1' }}>
                <p style={{ color: 'var(--text-muted)' }}>No se han encontrado artículos.</p>
                {searchTerm && <button className="btn btn-ghost" onClick={() => window.location.reload()}>Limpiar búsqueda</button>}
              </div>
            ) : (
              articles.map((article) => (
                <ArticleCard 
                  key={article.id_articulo} 
                  article={article} 
                  isFavorite={favorites.includes(String(article.id_articulo))}
                  onToggleFavorite={toggleFavorite}
                />
              ))
            )}
          </div>
        )}
      </div>

      <OfferModal
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
        onSuccess={(message) => setToast({ message, tone: 'success' })}
        onError={(message) => setToast({ message, tone: 'error' })}
      />

      <Toast
        message={toast.message}
        tone={toast.tone}
        onClose={() => setToast({ message: '', tone: 'success' })}
      />
    </div>
  )
}
