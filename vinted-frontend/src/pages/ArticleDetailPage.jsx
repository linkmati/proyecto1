import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import OfferModal from '../components/OfferModal'
import Toast from '../components/Toast'

export default function ArticleDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated, userId } = useAuth()
  const [article, setArticle] = useState(null)
  const [isFavorite, setIsFavorite] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showOfferModal, setShowOfferModal] = useState(false)
  const [toast, setToast] = useState({ message: '', tone: 'success' })
  const [activeImage, setActiveImage] = useState(0)

  const loadData = async () => {
    try {
      setLoading(true)
      try {
        const artRes = await api.get(`/api/articulos/${id}`)
        setArticle(artRes.data)
      } catch (err) {
        setToast({ message: 'El artículo no existe o hubo un error de conexión.', tone: 'error' })
        setLoading(false)
        return
      }

      if (isAuthenticated) {
        try {
          const favRes = await api.get('/api/favoritos')
          const favs = favRes.data || []
          setIsFavorite(favs.some(f => String(f.id_articulo) === String(id)))
        } catch (fErr) {
          console.warn('No favs loaded')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) loadData()
  }, [id, isAuthenticated])

  const toggleFav = async () => {
    if (!isAuthenticated) return navigate('/auth')
    try {
      if (isFavorite) {
        await api.delete(`/api/favoritos/${id}`)
      } else {
        await api.post(`/api/favoritos/${id}`)
      }
      setIsFavorite(!isFavorite)
    } catch (error) {
      setToast({ message: 'Error al actualizar favoritos.', tone: 'error' })
    }
  }

  const handleAskSeller = async () => {
    if (!isAuthenticated) return navigate('/auth')
    const content = prompt('Escribe tu mensaje para el vendedor:')
    if (!content || !content.trim()) return

    try {
      await api.post('/api/mensajes/', {
        id_destinatario: article.id_vendedor,
        id_articulo: article.id_articulo,
        contenido: content
      })
      setToast({ message: 'Mensaje enviado correctamente.', tone: 'success' })
      setTimeout(() => navigate('/mensajes'), 1500)
    } catch (error) {
      setToast({ message: 'No se pudo enviar el mensaje.', tone: 'error' })
    }
  }

  const nextImage = () => {
    if (!article?.fotos) return
    setActiveImage((prev) => (prev + 1) % article.fotos.length)
  }

  const prevImage = () => {
    if (!article?.fotos) return
    setActiveImage((prev) => (prev - 1 + article.fotos.length) % article.fotos.length)
  }

  if (loading) return <div className="container page-section"><div className="empty-state">Cargando detalles...</div></div>
  if (!article) return <div className="container page-section"><div className="card">Artículo no encontrado.</div></div>

  const isOwner = userId === article.id_vendedor

  return (
    <div className="container page-section">
      <div className="publish-layout" style={{ gridTemplateColumns: '400px 1fr', gap: '40px', alignItems: 'start' }}>
        
        {/* Galería de imágenes (MÁS PEQUEÑA) */}
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ position: 'relative', height: '350px', background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {article.fotos?.length > 0 ? (
              <img 
                src={article.fotos[activeImage].image_url} 
                alt={article.titulo} 
                style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} 
              />
            ) : (
              <div style={{ color: '#999' }}>Sin imágenes</div>
            )}
            
            {article.fotos?.length > 1 && (
              <>
                <button 
                  onClick={(e) => { e.stopPropagation(); prevImage(); }}
                  style={{ position: 'absolute', left: '10px', background: 'rgba(255,255,255,0.9)', border: 'none', width: '32px', height: '32px', borderRadius: '50%', cursor: 'pointer', display: 'grid', placeItems: 'center', boxShadow: 'var(--shadow)' }}
                >‹</button>
                <button 
                  onClick={(e) => { e.stopPropagation(); nextImage(); }}
                  style={{ position: 'absolute', right: '10px', background: 'rgba(255,255,255,0.9)', border: 'none', width: '32px', height: '32px', borderRadius: '50%', cursor: 'pointer', display: 'grid', placeItems: 'center', boxShadow: 'var(--shadow)' }}
                >›</button>
              </>
            )}

            <button 
              className="fav-btn" 
              onClick={toggleFav}
              style={{ position: 'absolute', top: '15px', right: '15px', width: '40px', height: '40px', fontSize: '1.3rem', color: isFavorite ? '#ef4444' : '#a3a3a3', background: 'white', borderRadius: '50%', border: 'none', boxShadow: 'var(--shadow)', cursor: 'pointer' }}
            >
              {isFavorite ? '❤️' : '🤍'}
            </button>
          </div>
          
          {article.fotos?.length > 1 && (
            <div style={{ display: 'flex', gap: '8px', padding: '12px', overflowX: 'auto', borderTop: '1px solid var(--line)' }}>
              {article.fotos.map((foto, idx) => (
                <img 
                  key={foto.id_foto}
                  src={foto.image_url} 
                  onClick={() => setActiveImage(idx)}
                  style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '6px', cursor: 'pointer', border: activeImage === idx ? '2px solid var(--primary)' : '1px solid var(--line)' }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Panel Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card">
            <div className="price" style={{ fontSize: '2rem', color: 'var(--primary)', marginBottom: '4px' }}>€ {Number(article.precio_base).toFixed(2)}</div>
            <h1 style={{ fontSize: '1.3rem', margin: '0 0 12px 0' }}>{article.titulo}</h1>
            <div className="badges" style={{ marginBottom: '20px' }}>
              <span className="badge">{article.estado_articulo}</span>
              <span className="badge badge--category">{article.categoria}</span>
            </div>

            {!isOwner ? (
              <div style={{ display: 'grid', gap: '10px' }}>
                <button className="button button--primary button--full" onClick={() => isAuthenticated ? setShowOfferModal(true) : navigate('/auth')}>
                  Hacer oferta
                </button>
                <button className="button button--secondary button--full" onClick={handleAskSeller}>
                  Preguntar al vendedor
                </button>
              </div>
            ) : (
              <button className="button button--secondary button--full" onClick={() => navigate('/perfil')}>
                Gestionar mi artículo
              </button>
            )}
          </div>

          <div className="card">
            <h2 style={{ fontSize: '0.9rem', marginBottom: '10px', textTransform: 'uppercase', color: 'var(--muted)' }}>Descripción</h2>
            <p style={{ color: 'var(--text)', whiteSpace: 'pre-wrap', lineHeight: '1.5', fontSize: '0.95rem' }}>{article.descripcion}</p>
          </div>
        </div>
      </div>

      {showOfferModal && (
        <OfferModal article={article} onClose={() => setShowOfferModal(false)} onSuccess={(m) => setToast({message: m, tone: 'success'})} onError={(m) => setToast({message: m, tone: 'error'})} />
      )}

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
