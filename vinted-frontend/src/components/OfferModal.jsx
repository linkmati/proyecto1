import { useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function OfferModal({ article, onClose, onSuccess, onError }) {
  const { isAuthenticated } = useAuth()
  const [importe, setImporte] = useState(article?.precio_base || '')
  const [mensaje, setMensaje] = useState('')
  const [loading, setLoading] = useState(false)

  if (!article) return null

  const isContraoferta = !!article.id_oferta

  const submitOffer = async (e) => {
    e.preventDefault()

    if (!isAuthenticated) {
      onError('Debes iniciar sesión para enviar una oferta.')
      return
    }

    try {
      setLoading(true)
      
      if (isContraoferta) {
        // Lógica de Contraoferta
        await api.patch(`/api/ofertas/${article.id_oferta}/contraoferta`, {
          nuevo_importe: Number(importe),
          mensaje,
        })
        onSuccess(`Contraoferta enviada correctamente.`)
      } else {
        // Lógica de Nueva Oferta
        const response = await api.post('/api/ofertas', {
          id_articulo: article.id_articulo,
          importe: Number(importe),
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
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <div>
            <span className="badge">{isContraoferta ? 'Contraoferta' : 'Nueva oferta'}</span>
            <h2>{article.titulo}</h2>
          </div>
          <button className="icon-button" onClick={onClose}>✕</button>
        </div>

        <form className="form" onSubmit={submitOffer}>
          <label>
            Importe {isContraoferta ? 'de la contraoferta' : 'ofertado'}
            <input
              type="number"
              min="0"
              step="0.01"
              value={importe}
              onChange={(e) => setImporte(e.target.value)}
              required
            />
          </label>

          <label>
            Mensaje opcional
            <textarea
              rows="4"
              value={mensaje}
              onChange={(e) => setMensaje(e.target.value)}
              placeholder="Ejemplo: ¿Te sirve entrega esta semana?"
            />
          </label>

          <button className="button button--primary button--full" disabled={loading}>
            {loading ? 'Enviando...' : (isContraoferta ? 'Enviar contraoferta' : 'Confirmar oferta')}
          </button>
        </form>
      </div>
    </div>
  )
}
