import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import Toast from '../components/Toast'
import { motion } from 'framer-motion'
import { ArrowLeft, Tag } from 'lucide-react'

export default function CounterOfferPage() {
  const { id } = useParams() // id de la oferta original
  const navigate = useNavigate()
  const [offer, setOffer] = useState(null)
  const [monto, setMonto] = useState('')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  useEffect(() => {
    const fetchOffer = async () => {
      try {
        const res = await api.get(`/api/offers/${id}`)
        setOffer(res.data)
        setMonto(res.data.monto_oferta)
      } catch (e) {
        setToast({ message: 'Error al cargar la oferta.', tone: 'error' })
      } finally {
        setLoading(false)
      }
    }
    fetchOffer()
  }, [id])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post(`/api/offers/${id}/counter`, { monto_oferta: parseFloat(monto) })
      setToast({ message: 'Contraoferta enviada con éxito', tone: 'success' })
      setTimeout(() => navigate('/mensajes'), 1500)
    } catch (error) {
      setToast({ message: 'Error al enviar contraoferta.', tone: 'error' })
    }
  }

  if (loading) return <div className="container" style={{ padding: '100px 0', textAlign: 'center' }}>Cargando...</div>

  return (
    <div className="container" style={{ padding: '40px 0', maxWidth: '600px' }}>
      <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ marginBottom: '24px' }}>
        <ArrowLeft size={20} />
        Volver
      </button>

      <div className="card" style={{ padding: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
          <div style={{ background: 'var(--primary-soft)', color: 'var(--primary)', padding: '12px', borderRadius: '12px' }}>
            <Tag size={32} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem' }}>Hacer una contraoferta</h1>
            <p style={{ color: 'var(--text-soft)' }}>Negocia el precio del artículo</p>
          </div>
        </div>

        {offer && (
          <div style={{ background: 'var(--bg-soft)', padding: '20px', borderRadius: '8px', marginBottom: '32px' }}>
            <div style={{ fontWeight: '600', marginBottom: '4px' }}>{offer.articulo_titulo}</div>
            <div style={{ color: 'var(--text-muted)' }}>Oferta actual: <strong>{offer.monto_oferta} €</strong></div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="form">
          <div>
            <label>Tu nuevo precio (€)</label>
            <input 
              type="number" 
              required 
              step="0.01" 
              className="search-input" 
              style={{ paddingLeft: '16px', fontSize: '1.2rem', fontWeight: '700' }}
              value={monto} 
              onChange={(e) => setMonto(e.target.value)} 
            />
          </div>

          <div style={{ marginTop: '32px', display: 'grid', gap: '12px' }}>
            <button type="submit" className="btn btn-primary" style={{ padding: '14px', borderRadius: '4px' }}>
              Enviar contraoferta
            </button>
          </div>
        </form>
      </div>

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
