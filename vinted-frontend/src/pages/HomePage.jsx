import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import ArticleCard from '../components/ArticleCard'
import Toast from '../components/Toast'
import OfferModal from '../components/OfferModal'

export default function HomePage() {
  const { isAuthenticated } = useAuth()
  const [articles, setArticles] = useState([])
  const [favorites, setFavorites] = useState([]) // List of article IDs (Strings)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('Todas')
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const CATEGORIAS = ['Todas', 'Moda', 'Hogar', 'Electrónica', 'Entretenimiento', 'Otros']

  const loadData = async () => {
    try {
      setLoading(true)
      const params = { limit: 20 }
      if (category !== 'Todas') params.categoria = category
      if (query.trim()) params.search = query.trim()
      
      const [artRes, favRes] = await Promise.all([
        api.get('/api/articulos', { params }).catch(() => ({ data: [] })),
        isAuthenticated ? api.get('/api/favoritos').catch(() => ({ data: [] })) : Promise.resolve({ data: [] })
      ])
      
      const fetchedArticles = Array.isArray(artRes.data) ? artRes.data : []
      setArticles(fetchedArticles)

      // CRÍTICO: Normalizar IDs a String para la comparación
      const favIds = (Array.isArray(favRes.data) ? favRes.data : []).map(f => String(f.id_articulo))
      setFavorites(favIds)
    } catch (error) {
      console.error('Error general en loadData:', error)
      setToast({ message: 'Error de conexión con el servidor.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // Debounce para la búsqueda por texto
  useEffect(() => {
    const timer = setTimeout(() => {
      loadData()
    }, 400)
    return () => clearTimeout(timer)
  }, [query, category, isAuthenticated])

  const onToggleFav = (id, isAdded) => {
    const idStr = String(id)
    if (isAdded) {
      setFavorites(prev => [...prev, idStr])
    } else {
      setFavorites(prev => prev.filter(favId => favId !== idStr))
    }
  }

  return (
    <div className="container page-section">
      <div className="hero" style={{ padding: '40px 0', textAlign: 'center' }}>
        <span className="eyebrow">Segunda mano con estilo</span>
        <h1 style={{ fontSize: '3rem', margin: '16px 0' }}>Encuentra tesoros únicos</h1>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <input
            className="search-input"
            style={{ maxWidth: '100%', padding: '16px 24px', fontSize: '1.1rem' }}
            placeholder="¿Qué estás buscando?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="categories-bar">
        {CATEGORIAS.map(cat => (
          <div 
            key={cat} 
            className={`category-pill ${category === cat ? 'category-pill--active' : ''}`}
            onClick={() => setCategory(cat)}
          >
            {cat}
          </div>
        ))}
      </div>

      <div className="section-heading">
        <h2>{category === 'Todas' ? 'Últimas novedades' : `Novedades en ${category}`}</h2>
      </div>

      {loading ? (
        <div className="empty-state">Buscando...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">No se han encontrado artículos.</div>
      ) : (
        <div className="article-grid">
          {articles.map((article) => {
            const artIdStr = String(article.id_articulo)
            const isFav = favorites.includes(artIdStr)
            
            return (
              <ArticleCard 
                key={article.id_articulo} 
                article={article} 
                onOffer={setSelectedArticle} 
                isFavorite={isFav}
                onToggleFav={onToggleFav}
              />
            )
          })}
        </div>
      )}

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
