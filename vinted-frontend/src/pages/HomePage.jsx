import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import Hero from '../components/Hero'
import ArticleCard from '../components/ArticleCard'
import OfferModal from '../components/OfferModal'
import Toast from '../components/Toast'

export default function HomePage() {
  const [articles, setArticles] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const loadArticles = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/articulos')
      setArticles(response.data)
    } catch (error) {
      setToast({
        message: error.response?.data?.detail || 'No se pudieron cargar los artículos.',
        tone: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadArticles()
  }, [])

  const filteredArticles = useMemo(() => {
    const text = query.toLowerCase()
    return articles.filter((article) => {
      return (
        article.titulo?.toLowerCase().includes(text) ||
        article.descripcion?.toLowerCase().includes(text)
      )
    })
  }, [articles, query])

  return (
    <>
      <Hero />
      <section className="container page-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Catálogo activo</span>
            <h2>Artículos disponibles</h2>
          </div>
          <input
            className="search-input"
            placeholder="Buscar por título o descripción"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="empty-state">Cargando artículos...</div>
        ) : filteredArticles.length === 0 ? (
          <div className="empty-state">No hay artículos que coincidan con tu búsqueda.</div>
        ) : (
          <div className="article-grid">
            {filteredArticles.map((article) => (
              <ArticleCard key={article.id_articulo} article={article} onOffer={setSelectedArticle} />
            ))}
          </div>
        )}
      </section>

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
    </>
  )
}
