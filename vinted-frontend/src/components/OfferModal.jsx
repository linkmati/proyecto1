import React, { useState, useEffect } from 'react'
import api from '../api/client'
import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function OfferModal({ article, onClose, onSuccess, onError }) {
  const [importe, setImporte] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (article) {
      setImporte(article.precio_base || article.precio || '')
      setMensaje('')
    }
  }, [article?.id_articulo, article?.id_oferta])

  if (!article) return null

  const isContraoferta = !!article.id_oferta

  const submitOffer = async (e) => {
    e.preventDefault()
    if (!importe || loading) return

    try {
      setLoading(true)
      
      if (isContraoferta) {
        await api.patch(`/api/offers/${article.id_oferta}/counter-offer`, {
          nuevo_importe: parseFloat(importe),
          mensaje: mensaje || undefined
        })
        onSuccess(`Contraoferta enviada correctamente.`)
      } else {
        await api.post('/api/offers', {
          id_articulo: article.id_articulo,
          importe: parseFloat(importe),
          mensaje,
        })
        onSuccess(`Oferta enviada correctamente.`)
      }
      
      onClose()
    } catch (error) {
      onError(error.response?.data?.detail || 'No se pudo procesar la oferta.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      <div className="modal-overlay" onClick={onClose}>
        <motion.div 
          className="modal-content" 
          onClick={(e) => e.stopPropagation()}
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <div>
              <span className="badge" style={{ background: 'var(--primary-soft)', color: 'var(--primary)', marginBottom: '8px' }}>
                {isContraoferta ? 'Contraoferta' : 'Hacer una oferta'}
              </span>
              <h2 style={{ fontSize: '1.25rem' }}>{article.titulo}</h2>
            </div>
            <button className="btn btn-ghost" style={{ padding: '8px' }} onClick={onClose}>
              <X size={24} />
            </button>
          </div>

          <form onSubmit={submitOffer} style={{ display: 'grid', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '0.9rem' }}>
                Tu precio ofertado (€)
              </label>
              <input
                autoFocus
                className="search-input"
                style={{ paddingLeft: '16px', fontSize: '1.1rem', fontWeight: '700' }}
                type="number"
                min="0"
                step="0.01"
                value={importe}
                onChange={(e) => setImporte(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '0.9rem' }}>
                Mensaje (opcional)
              </label>
              <textarea
                className="search-input"
                style={{ padding: '12px 16px', minHeight: '100px', resize: 'none' }}
                value={mensaje}
                onChange={(e) => setMensaje(e.target.value)}
                placeholder="Ej: Hola, ¿me lo dejas por este precio?"
              />
            </div>

            <button className="btn btn-primary" style={{ width: '100%', padding: '14px', borderRadius: '4px' }} disabled={loading}>
              {loading ? 'Enviando...' : 'Enviar oferta'}
            </button>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
