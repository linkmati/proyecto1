import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'

export default function MessagesPage() {
  const { userId } = useAuth()
  const [conversations, setConversations] = useState([])
  const [selectedConv, setSelectedConv] = useState(null)
  const [messages, setMessages] = useState([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const loadConversations = async () => {
    try {
      setLoading(true)
      const res = await api.get('/api/mensajes/conversaciones')
      setConversations(res.data)
    } catch (error) {
      setToast({ message: 'Error cargando conversaciones.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async (id) => {
    try {
      const res = await api.get(`/api/mensajes/conversaciones/${id}`)
      setMessages(res.data)
      setSelectedConv(id)
    } catch (error) {
      setToast({ message: 'Error cargando mensajes.', tone: 'error' })
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
    } catch (error) {
      setToast({ message: 'Error al enviar mensaje.', tone: 'error' })
    }
  }

  useEffect(() => {
    loadConversations()
  }, [])

  if (loading) return <div className="container page-section">Cargando chats...</div>

  return (
    <div className="container page-section publish-layout" style={{ gridTemplateColumns: '300px 1fr', height: 'calc(100vh - 160px)' }}>
      <div className="card" style={{ overflowY: 'auto', padding: '12px' }}>
        <h2 style={{ padding: '12px' }}>Chats</h2>
        {conversations.length === 0 ? (
          <div className="empty-state">No hay conversaciones.</div>
        ) : (
          conversations.map(c => (
            <div 
              key={c.id_conversacion} 
              className={`card ${selectedConv === c.id_conversacion ? 'tab--active' : ''}`}
              style={{ cursor: 'pointer', marginBottom: '8px', padding: '12px' }}
              onClick={() => loadMessages(c.id_conversacion)}
            >
              <strong>Chat #{c.id_conversacion}</strong>
              <small style={{ display: 'block' }}>Artículo ID: {c.id_articulo}</small>
            </div>
          ))
        )}
      </div>

      <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: '0' }}>
        {selectedConv ? (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {messages.map(m => (
                <div key={m.id_mensaje} style={{ 
                  alignSelf: m.id_emisor === userId ? 'flex-end' : 'flex-start',
                  background: m.id_emisor === userId ? 'var(--primary)' : 'var(--bg-soft)',
                  padding: '12px 16px',
                  borderRadius: '16px',
                  maxWidth: '70%',
                  color: 'white'
                }}>
                  {m.contenido}
                </div>
              ))}
            </div>
            <form className="form" style={{ padding: '24px', borderTop: '1px solid var(--line)', display: 'flex', gap: '12px' }} onSubmit={sendMessage}>
              <input 
                placeholder="Escribe un mensaje..." 
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
              <button className="button button--primary">Enviar</button>
            </form>
          </>
        ) : (
          <div className="empty-state" style={{ margin: 'auto' }}>Selecciona un chat para empezar</div>
        )}
      </div>

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
