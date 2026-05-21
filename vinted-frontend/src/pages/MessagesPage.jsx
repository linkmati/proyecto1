import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import OfferModal from '../components/OfferModal'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, User, Inbox, Tag, Check, CheckCheck, XCircle, CheckCircle, RefreshCcw } from 'lucide-react'

export default function MessagesPage() {
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const toId = searchParams.get('to')
  const itemId = searchParams.get('item')

  const [conversations, setConversations] = useState([])
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [activeOffer, setActiveOffer] = useState(null)
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCounterModal, setShowCounterModal] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation.id_conversacion)
      markAsRead(selectedConversation.id_conversacion)
      const interval = setInterval(() => loadMessages(selectedConversation.id_conversacion), 5000)
      return () => clearInterval(interval)
    }
  }, [selectedConversation])

  useEffect(() => {
    if (conversations.length > 0) {
      let targetConv = null;
      if (toId) {
        targetConv = conversations.find(c => 
          (String(c.id_usuario_1) === String(toId) || String(c.id_usuario_2) === String(toId)) &&
          (!itemId || String(c.id_articulo) === String(itemId))
        )
      }
      
      if (targetConv) {
        setSelectedConversation(targetConv)
      } else if (!selectedConversation) {
        setSelectedConversation(conversations[0])
      }
    }
  }, [toId, itemId, conversations])

  useEffect(scrollToBottom, [messages])

  const loadConversations = async () => {
    try {
      const res = await api.get('/api/messages/conversations')
      setConversations(res.data)
    } catch (e) {
      console.error("Error loading conversations", e)
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async (convId) => {
    try {
      const res = await api.get(`/api/messages/conversations/${convId}/messages`)
      setMessages(res.data.messages)
      setActiveOffer(res.data.offer)
    } catch (e) {}
  }

  const markAsRead = async (convId) => {
    try {
      await api.patch(`/api/messages/conversations/${convId}/read`)
      // Refresh list to update counts
      loadConversations()
    } catch (e) {}
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!newMessage.trim() || !selectedConversation) return
    const content = newMessage
    setNewMessage('')
    
    try {
      await api.post('/api/messages', {
        id_destinatario: String(selectedConversation.id_usuario_1) === String(user.id_usuario) 
          ? selectedConversation.id_usuario_2 
          : selectedConversation.id_usuario_1,
        id_articulo: selectedConversation.id_articulo,
        contenido: content
      })
      loadMessages(selectedConversation.id_conversacion)
      setTimeout(loadConversations, 500)
    } catch (e) {
      setNewMessage(content)
    }
  }

  const handleOfferAction = async (action) => {
    if (!activeOffer) return
    try {
      await api.post(`/api/offers/${activeOffer.id_oferta}/${action}`)
      loadMessages(selectedConversation.id_conversacion)
      loadConversations()
    } catch (e) {
      alert("No se pudo realizar la acción")
    }
  }

  return (
    <div className="container" style={{ padding: '24px 0', height: 'calc(100vh - var(--header-height) - 48px)', display: 'flex', gap: '2px' }}>
      {/* Sidebar */}
      <div className="card" style={{ width: '380px', padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', borderRadius: 'var(--radius-md) 0 0 var(--radius-md)' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid var(--line)' }}>
          <h2 style={{ fontSize: '1.2rem' }}>Mensajes</h2>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>Cargando conversaciones...</div>
          ) : conversations.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-soft)' }}>
              <Inbox size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
              <p>No tienes mensajes todavía.</p>
            </div>
          ) : (
            conversations.map(conv => (
              <div 
                key={conv.id_conversacion} 
                onClick={() => setSelectedConversation(conv)}
                style={{ 
                  padding: '20px 24px', 
                  cursor: 'pointer', 
                  borderBottom: '1px solid var(--line)',
                  background: selectedConversation?.id_conversacion === conv.id_conversacion ? 'var(--primary-soft)' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}
              >
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--line)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                  <User size={24} color="var(--text-soft)" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>{conv.other_user_name}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-soft)' }}>
                      {new Date(conv.last_activity).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--primary)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Tag size={12} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{conv.item_title}</span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {conv.last_message}
                  </div>
                </div>
                {conv.unread_count > 0 && (
                  <div style={{ background: 'var(--primary)', color: 'white', fontSize: '0.7rem', minWidth: '20px', height: '20px', padding: '0 6px', borderRadius: '10px', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>
                    {conv.unread_count}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="card" style={{ flex: 1, padding: 0, display: 'flex', flexDirection: 'column', borderRadius: '0 var(--radius-md) var(--radius-md) 0', borderLeft: 'none' }}>
        {selectedConversation ? (
          <>
            <div style={{ padding: '16px 32px', borderBottom: '1px solid var(--line)', background: 'white' }}>
               <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                 <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'var(--bg-soft)', display: 'grid', placeItems: 'center' }}>
                  <User size={24} color="var(--primary)" />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.1rem' }}>{selectedConversation.other_user_name}</h3>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{selectedConversation.item_title}</div>
                </div>
               </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '32px', display: 'flex', flexDirection: 'column', gap: '16px', background: '#f0f2f5' }}>
              
              {/* Offer Card in Chat */}
              {activeOffer && (
                <div style={{ alignSelf: 'center', width: '100%', maxWidth: '400px', marginBottom: '24px' }}>
                   <div className="card" style={{ padding: '24px', textAlign: 'center', background: 'white', borderTop: '4px solid var(--primary)' }}>
                      <div style={{ color: 'var(--text-soft)', fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: '700', marginBottom: '8px' }}>
                        Oferta {activeOffer.estado}
                      </div>
                      <div style={{ fontSize: '2rem', fontWeight: '800', marginBottom: '16px' }}>{activeOffer.importe} €</div>
                      
                      {activeOffer.estado === 'pendiente' && (
                        <div style={{ display: 'grid', gridTemplateColumns: activeOffer.ultimo_emisor_id !== user.id_usuario ? '1fr 1fr' : '1fr', gap: '12px' }}>
                           {activeOffer.ultimo_emisor_id !== user.id_usuario ? (
                             <>
                               <button className="btn btn-primary" onClick={() => handleOfferAction('accept')}>Aceptar</button>
                               <button className="btn btn-secondary" style={{ color: '#ef4444' }} onClick={() => handleOfferAction('reject')}>Rechazar</button>
                               <button 
                                 className="btn btn-secondary" 
                                 style={{ gridColumn: '1/-1' }}
                                 onClick={() => setShowCounterModal(true)}
                               >
                                 <RefreshCcw size={16} /> Hacer contraoferta
                               </button>
                             </>
                           ) : (
                             <p style={{ color: 'var(--text-soft)', fontSize: '0.9rem' }}>Esperando respuesta...</p>
                           )}
                        </div>
                      )}
                      
                      {activeOffer.estado === 'aceptada' && (
                        <div style={{ color: '#166534', background: '#dcfce7', padding: '10px', borderRadius: '4px', fontWeight: '600' }}>
                           <CheckCircle size={18} inline /> ¡Oferta aceptada!
                        </div>
                      )}
                      {activeOffer.estado === 'rechazada' && (
                        <div style={{ color: '#991b1b', background: '#fee2e2', padding: '10px', borderRadius: '4px', fontWeight: '600' }}>
                           <XCircle size={18} inline /> Oferta rechazada
                        </div>
                      )}
                   </div>
                </div>
              )}

              {messages.map(msg => (
                <div 
                  key={msg.id_mensaje} 
                  style={{ 
                    alignSelf: String(msg.id_emisor) === String(user.id_usuario) ? 'flex-end' : 'flex-start',
                    maxWidth: '70%',
                    padding: '12px 18px',
                    borderRadius: String(msg.id_emisor) === String(user.id_usuario) ? '18px 18px 2px 18px' : '18px 18px 18px 2px',
                    background: String(msg.id_emisor) === String(user.id_usuario) ? 'var(--primary)' : 'white',
                    color: String(msg.id_emisor) === String(user.id_usuario) ? 'white' : 'var(--text)',
                    boxShadow: '0 1px 1px rgba(0,0,0,0.05)'
                  }}
                >
                  <div style={{ fontSize: '0.95rem' }}>{msg.contenido}</div>
                  <div style={{ fontSize: '0.65rem', marginTop: '4px', opacity: 0.8, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '4px' }}>
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {String(msg.id_emisor) === String(user.id_usuario) && (
                      msg.leido ? <CheckCheck size={14} color="#93c5fd" /> : <Check size={14} />
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSend} style={{ padding: '20px 32px', background: 'white', borderTop: '1px solid var(--line)', display: 'flex', gap: '12px' }}>
              <input 
                className="search-input" 
                style={{ flex: 1, paddingLeft: '20px', borderRadius: 'var(--radius-full)' }} 
                placeholder="Escribe un mensaje..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
              />
              <button type="submit" className="btn btn-primary" style={{ width: '44px', height: '44px', padding: 0, borderRadius: '50%' }}>
                <Send size={20} />
              </button>
            </form>
          </>
        ) : (
          <div style={{ flex: 1, display: 'grid', placeItems: 'center', color: 'var(--text-soft)', background: 'var(--bg-soft)' }}>
            <div style={{ textAlign: 'center' }}>
              <Inbox size={64} style={{ marginBottom: '16px', opacity: 0.2 }} />
              <p>Selecciona una conversación para empezar a chatear</p>
            </div>
          </div>
        )}
      </div>

      {/* Counter-offer Modal Wrapper */}
      {showCounterModal && (
        <OfferModal 
           article={{ 
             id_articulo: selectedConversation.id_articulo,
             titulo: selectedConversation.item_title,
             id_oferta: activeOffer?.id_oferta
           }}
           onClose={() => setShowCounterModal(false)}
           onSuccess={() => {
             setShowCounterModal(false)
             loadMessages(selectedConversation.id_conversacion)
           }}
           onError={(m) => alert(m)}
        />
      )}
    </div>
  )
}
