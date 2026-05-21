import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'
import OfferModal from '../components/OfferModal'
import { motion } from 'framer-motion'
import { ShieldCheck, MessageCircle, Heart, Share2, Tag, Send, User } from 'lucide-react'

export default function ArticleDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isFavorite, setIsFavorite] = useState(false)
  const [selectedOffer, setSelectedOffer] = useState(null)
  const [toast, setToast] = useState({ message: '', tone: 'success' })
  
  const [showChatBox, setShowChatBox] = useState(false)
  const [firstMessage, setFirstMessage] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [artRes, favRes] = await Promise.all([
          api.get(`/api/items/${id}`),
          user ? api.get('/api/favorites') : Promise.resolve({ data: [] })
        ])
        setArticle(artRes.data)
        setIsFavorite(favRes.data.some(f => String(f.id_articulo) === String(id)))
      } catch (error) {
        setToast({ message: 'No se pudo cargar el artículo.', tone: 'error' })
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [id, user])

  const toggleFavorite = async () => {
    if (!user) {
      setToast({ message: 'Inicia sesión para guardar favoritos.', tone: 'error' })
      return
    }

    const previousState = isFavorite
    setIsFavorite(!previousState) // Optimistic update

    try {
      if (previousState) {
        await api.delete(`/api/favorites/${id}`)
      } else {
        await api.post(`/api/favorites/${id}`)
      }
    } catch (e) {
      setIsFavorite(previousState)
      setToast({ message: 'Error al actualizar favoritos.', tone: 'error' })
    }
  }

  const handleShare = async () => {
    const shareData = {
      title: article.titulo,
      text: `Mira este artículo en Mas Tienda: ${article.titulo}`,
      url: window.location.href
    }

    try {
      if (navigator.share) {
        await navigator.share(shareData)
      } else {
        await navigator.clipboard.writeText(window.location.href)
        setToast({ message: 'Enlace copiado al portapapeles', tone: 'success' })
      }
    } catch (err) {
      console.error('Error al compartir:', err)
    }
  }

  const handleStartChat = async (e) => {
    e.preventDefault()
    if (!firstMessage.trim()) return
    try {
      await api.post('/api/messages', {
        id_destinatario: article.id_vendedor,
        id_articulo: article.id_articulo,
        contenido: firstMessage
      })
      setToast({ message: 'Mensaje enviado!', tone: 'success' })
      setTimeout(() => navigate(`/mensajes?to=${article.id_vendedor}&item=${article.id_articulo}`), 1000)
    } catch (error) {
      setToast({ message: 'Error al enviar mensaje.', tone: 'error' })
    }
  }

  if (loading) return <div className="container" style={{ padding: '100px 0', textAlign: 'center' }}>Cargando...</div>
  if (!article) return <div className="container" style={{ padding: '100px 0', textAlign: 'center' }}>Artículo no encontrado</div>

  return (
    <div className="container" style={{ padding: '40px 0' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '40px' }}>
        {/* Images */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ display: 'grid', gap: '16px' }}
        >
          {article.fotos?.length > 0 ? (
            article.fotos.map((foto, idx) => (
              <img 
                key={idx} 
                src={foto.image_url} 
                alt={article.titulo} 
                style={{ width: '100%', borderRadius: 'var(--radius-md)', border: '1px solid var(--line)' }}
              />
            ))
          ) : (
            <div style={{ aspectRatio: '4/5', background: 'var(--bg-soft)', borderRadius: 'var(--radius-md)', display: 'grid', placeItems: 'center' }}>
              Sin imágenes
            </div>
          )}
        </motion.div>

        {/* Info */}
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ position: 'sticky', top: '112px', height: 'fit-content' }}
        >
          <div className="card" style={{ padding: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>{article.precio_base || article.precio} €</h1>
                <div style={{ color: 'var(--text-soft)', fontSize: '1.1rem' }}>{article.titulo}</div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  className="btn btn-secondary" 
                  style={{ padding: '10px' }} 
                  onClick={toggleFavorite}
                  title="Guardar en favoritos"
                >
                  <Heart size={20} fill={isFavorite ? '#ef4444' : 'none'} color={isFavorite ? '#ef4444' : 'currentColor'} />
                </button>
                <button 
                  className="btn btn-secondary" 
                  style={{ padding: '10px' }}
                  onClick={handleShare}
                  title="Compartir artículo"
                >
                  <Share2 size={20} />
                </button>
              </div>
            </div>

            {/* Seller Info Section */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px', 
              padding: '16px', 
              background: 'var(--bg-soft)', 
              borderRadius: 'var(--radius-sm)',
              marginBottom: '24px',
              border: '1px solid var(--line)'
            }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--primary-soft)', color: 'var(--primary)', display: 'grid', placeItems: 'center' }}>
                <User size={20} />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-soft)', textTransform: 'uppercase', fontWeight: '700', letterSpacing: '0.05em' }}>Vendedor</div>
                <div style={{ fontWeight: '600', color: 'var(--text)' }}>{article.vendedor_nombre}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '32px' }}>
              <span className="badge badge-success">{article.estado_articulo}</span>
              <span className="badge" style={{ background: 'var(--surface-muted)' }}>{article.categoria}</span>
            </div>

            <div style={{ borderTop: '1px solid var(--line)', padding: '24px 0' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '12px' }}>Descripción</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                {article.descripcion}
              </p>
            </div>

            <div style={{ display: 'grid', gap: '12px' }}>
              {user?.id_usuario !== article.id_vendedor ? (
                <>
                  <button className="btn btn-primary" onClick={() => setSelectedOffer(article)} style={{ width: '100%', padding: '16px', borderRadius: '4px' }}>
                    <Tag size={20} />
                    Hacer una oferta
                  </button>
                  
                  {!showChatBox ? (
                    <button className="btn btn-secondary" onClick={() => setShowChatBox(true)} style={{ width: '100%', padding: '16px', borderRadius: '4px' }}>
                      <MessageCircle size={20} />
                      Enviar mensaje
                    </button>
                  ) : (
                    <motion.form 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      onSubmit={handleStartChat}
                      style={{ display: 'flex', gap: '8px' }}
                    >
                      <input 
                        autoFocus
                        className="search-input" 
                        style={{ flex: 1, paddingLeft: '12px' }} 
                        placeholder="Escribe tu mensaje..."
                        value={firstMessage}
                        onChange={(e) => setFirstMessage(e.target.value)}
                      />
                      <button type="submit" className="btn btn-primary" style={{ padding: '12px' }}>
                        <Send size={20} />
                      </button>
                    </motion.form>
                  )}
                </>
              ) : (
                <button className="btn btn-secondary" style={{ width: '100%', padding: '16px', borderRadius: '4px' }} disabled>
                  Es tu artículo
                </button>
              )}
            </div>

            <div style={{ marginTop: '24px', display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: 'var(--primary-soft)', borderRadius: 'var(--radius-sm)', color: 'var(--primary)' }}>
               <ShieldCheck size={24} />
               <div style={{ fontSize: '0.85rem' }}>
                 <strong>Compra segura.</strong> Tu dinero está protegido hasta que recibas el producto.
               </div>
            </div>
          </div>
        </motion.div>
      </div>

      <OfferModal
        article={selectedOffer}
        onClose={() => setSelectedOffer(null)}
        onSuccess={(m) => setToast({ message: m, tone: 'success' })}
        onError={(m) => setToast({ message: m, tone: 'error' })}
      />

      <Toast
        message={toast.message}
        tone={toast.tone}
        onClose={() => setToast({ message: '', tone: 'success' })}
      />
    </div>
  )
}
