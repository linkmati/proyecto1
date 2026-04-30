import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'
import OfferModal from '../components/OfferModal'

export default function MessagesPage() {
  const { userId } = useAuth()
  const [conversations, setConversations] = useState([])
  const [selectedConv, setSelectedConv] = useState(null)
  const [messages, setMessages] = useState([])
  const [offers, setOffers] = useState([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const loadConversations = async () => {
    try {
      setLoading(true)
      const [cRes, oRes] = await Promise.all([
        api.get('/api/mensajes/conversaciones'),
        api.get('/api/ofertas')
      ])
      setConversations(cRes.data)
      setOffers(oRes.data)
    } catch (error) {
      setToast({ message: 'Error cargando datos.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async (id) => {
    try {
      const res = await api.get(`/api/mensajes/conversaciones/${id}`)
      setMessages(res.data)
      setSelectedConv(id)
      
      // Marcar como leído
      await api.patch(`/api/mensajes/conversaciones/${id}/leer`)
      
      // Refresh list to clear notification badge locally
      const cRes = await api.get('/api/mensajes/conversaciones')
      setConversations(cRes.data)
    } catch (error) {
      console.error('Error cargando mensajes:', error)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!content.trim() || !selectedConv) return

    const conv = conversations.find(c => c.id_conversacion === selectedConv)
    const recipientId = conv.id_usuario_1 === userId ? conv.id_usuario_2 : conv.id_usuario_1

    try {
      await api.post('/api/mensajes/', {
        id_destinatario: recipientId,
        id_articulo: conv.id_articulo,
        contenido: content
      })
      setContent('')
      loadMessages(selectedConv)
      // loadMessages already refreshes conversations list
    } catch (error) {
      setToast({ message: 'Error al enviar mensaje.', tone: 'error' })
    }
  }

  const handleOfferAction = async (id, action) => {
    try {
      await api.post(`/api/ofertas/${id}/${action}`)
      setToast({ message: `Oferta ${action} con éxito.`, tone: 'success' })
      loadConversations() // refresh offers and re-sort list
      if (selectedConv) loadMessages(selectedConv)
    } catch (error) {
      setToast({ message: 'Error en la oferta.', tone: 'error' })
    }
  }

  useEffect(() => {
    loadConversations()
  }, [])

  const currentConv = conversations.find(c => c.id_conversacion === selectedConv)
  const currentOffer = currentConv ? offers.find(o => o.id_articulo === currentConv.id_articulo && o.estado === 'pendiente') : null
  
  const isSeller = currentOffer && currentOffer.id_comprador !== userId
  const isMyTurn = currentOffer && currentOffer.ultimo_emisor_id !== userId

  if (loading) return <div className="container page-section">Cargando...</div>

  return (
    <div className="container page-section" style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px', height: 'calc(100vh - 120px)' }}>
      <div className="card" style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ padding: '20px' }}>Mensajes</h2>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {conversations.map(c => (
            <div 
              key={c.id_conversacion} 
              className={`tab ${selectedConv === c.id_conversacion ? 'tab--active' : ''}`}
              style={{ borderBottom: '1px solid var(--line)', padding: '16px 20px', cursor: 'pointer', position: 'relative' }}
              onClick={() => loadMessages(c.id_conversacion)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 'bold', fontSize: '1rem', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.titulo_articulo}
                </div>
                {c.unread_count > 0 && (
                  <div style={{ 
                    background: 'var(--accent)', 
                    color: 'white', 
                    borderRadius: '50%', 
                    width: '18px', 
                    height: '18px', 
                    fontSize: '0.7rem', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    marginLeft: '8px',
                    flexShrink: 0
                  }}>
                    {c.unread_count}
                  </div>
                )}
              </div>
              <small style={{ display: 'block', color: 'var(--muted)', marginTop: '4px' }}>
                Con: {c.nombre_otro}
              </small>
            </div>
          ))}
          {conversations.length === 0 && <div style={{ padding: '20px', textAlign: 'center', color: 'var(--muted)' }}>No tienes mensajes aún</div>}
        </div>
      </div>

      <div className="card" style={{ padding: '0', display: 'flex', flexDirection: 'column' }}>
        {selectedConv ? (
          <>
            <div style={{ padding: '12px 24px', borderBottom: '1px solid var(--line)', background: 'var(--bg-soft)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
               <div>
                <Link to={`/articulo/${currentConv.id_articulo}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <strong>{currentConv.titulo_articulo} ↗</strong>
                </Link> 
                <span style={{ color: 'var(--muted)', margin: '0 8px' }}>—</span> 
                {currentConv.nombre_otro}
               </div>
               <button 
                className="button button--ghost" 
                style={{ fontSize: '0.8rem', padding: '4px 12px' }}
                onClick={() => setSelectedArticle({ 
                  id_articulo: currentConv.id_articulo, 
                  titulo: currentConv.titulo_articulo,
                  id_oferta: currentOffer?.id_oferta 
                })}
               >
                 {isSeller ? 'Hacer Contraoferta' : 'Nueva Oferta'}
               </button>
            </div>
            
            {currentOffer && isMyTurn && (
              <div style={{ padding: '16px 24px', background: 'white', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span className="eyebrow" style={{ fontSize: '0.7rem' }}>Oferta pendiente</span>
                  <div style={{ fontWeight: 'bold' }}>
                    {currentOffer.ultimo_emisor_id === currentOffer.id_comprador 
                      ? `${currentOffer.nombre_comprador} te ha hecho una oferta de €${currentOffer.importe}`
                      : `El vendedor te ha hecho una contraoferta de €${currentOffer.importe}`
                    }
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="button button--primary" onClick={() => handleOfferAction(currentOffer.id_oferta, 'aceptar')}>Aceptar</button>
                  <button className="button button--secondary" onClick={() => handleOfferAction(currentOffer.id_oferta, 'rechazar')}>Rechazar</button>
                </div>
              </div>
            )}

            <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {messages.map(m => (
                <div key={m.id_mensaje} style={{ 
                  alignSelf: m.id_emisor === userId ? 'flex-end' : 'flex-start',
                  background: m.id_emisor === userId ? 'var(--primary)' : 'var(--bg-soft)',
                  color: m.id_emisor === userId ? 'white' : 'inherit',
                  padding: '10px 16px',
                  borderRadius: '12px',
                  maxWidth: '70%',
                  position: 'relative'
                }}>
                  {m.contenido}
                  {m.id_emisor === userId && (
                    <span style={{ 
                      fontSize: '0.7rem', 
                      marginLeft: '8px', 
                      opacity: 0.8,
                      verticalAlign: 'bottom'
                    }}>
                      {m.leido ? '✓✓' : '✓'}
                    </span>
                  )}
                </div>
              ))}
            </div>

            <form style={{ padding: '20px', borderTop: '1px solid var(--line)', display: 'flex', gap: '12px' }} onSubmit={sendMessage}>
              <input 
                placeholder="Escribe un mensaje..." 
                value={content}
                onChange={(e) => setContent(e.target.value)}
                style={{ flex: 1 }}
              />
              <button className="button button--primary">Enviar</button>
            </form>
          </>
        ) : (
          <div className="empty-state" style={{ margin: 'auto' }}>Selecciona un chat</div>
        )}
      </div>

      <OfferModal
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
        onSuccess={(msg) => {
          setToast({ message: msg, tone: 'success' })
          loadConversations()
          if (selectedConv) loadMessages(selectedConv)
        }}
        onError={(msg) => setToast({ message: msg, tone: 'error' })}
      />

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
