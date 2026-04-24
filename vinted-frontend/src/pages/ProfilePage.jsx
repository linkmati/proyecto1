import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'

export default function ProfilePage() {
  const { userEmail } = useAuth()
  const [profile, setProfile] = useState(null)
  const [articles, setArticles] = useState([])
  const [offers, setOffers] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const loadData = async () => {
    try {
      setLoading(true)
      const [pRes, aRes, oRes] = await Promise.all([
        api.get('/api/users/me'),
        api.get('/api/users/me/articulos'),
        api.get('/api/ofertas')
      ])
      setProfile(pRes.data)
      setArticles(aRes.data)
      setOffers(oRes.data)
    } catch (error) {
      setToast({ message: 'Error cargando datos del perfil.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleOfferAction = async (id, action) => {
    try {
      await api.post(`/api/ofertas/${id}/${action}`)
      setToast({ message: `Oferta ${action === 'aceptar' ? 'aceptada' : 'rechazada'} correctamente.`, tone: 'success' })
      loadData()
    } catch (error) {
      setToast({ message: `Error al ${action} la oferta.`, tone: 'error' })
    }
  }

  if (loading) return <div className="container page-section">Cargando...</div>

  return (
    <div className="container page-section">
      <div className="spotlight-card card" style={{ marginBottom: '24px' }}>
        <span className="eyebrow">Mi Perfil</span>
        <h1>Hola, {profile?.email}</h1>
        <p>Estado de cuenta: <strong>{profile?.estado}</strong></p>
      </div>

      <div className="publish-layout">
        <div>
          <h2>Mis Artículos</h2>
          {articles.length === 0 ? (
            <div className="empty-state">No has publicado nada todavía.</div>
          ) : (
            <div className="meta-grid" style={{ gap: '16px' }}>
              {articles.map(art => (
                <div key={art.id_articulo} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{art.titulo}</strong>
                    <small>{art.estado_articulo} - €{art.precio_base}</small>
                  </div>
                  <span className="badge">{art.categoria}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2>Gestión de Ofertas</h2>
          {offers.filter(o => o.estado === 'pendiente').length === 0 ? (
            <div className="empty-state">No tienes ofertas pendientes.</div>
          ) : (
            <div className="meta-grid" style={{ gap: '16px' }}>
              {offers.filter(o => o.estado === 'pendiente').map(off => (
                <div key={off.id_oferta} className="card">
                  <div style={{ marginBottom: '12px' }}>
                    <strong>Oferta de €{off.importe}</strong>
                    <p style={{ margin: '4px 0', fontSize: '0.9rem' }}>{off.mensaje || 'Sin mensaje'}</p>
                    <small>Artículo ID: {off.id_articulo}</small>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="button button--primary" onClick={() => handleOfferAction(off.id_oferta, 'aceptar')}>Aceptar</button>
                    <button className="button button--secondary" onClick={() => handleOfferAction(off.id_oferta, 'rechazar')}>Rechazar</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
