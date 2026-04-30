import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import ArticleCard from '../components/ArticleCard'
import Toast from '../components/Toast'

export default function ProfilePage() {
  const { userEmail, isAuthenticated } = useAuth()
  const [activeTab, setActiveTab] = useState('publicados')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const loadData = async () => {
    if (!isAuthenticated) return
    try {
      setLoading(true)
      let endpoint = ''
      if (activeTab === 'publicados') endpoint = '/api/users/me/articulos'
      if (activeTab === 'compras') endpoint = '/api/users/me/compras'
      if (activeTab === 'favoritos') endpoint = '/api/favoritos'

      const res = await api.get(endpoint).catch(() => ({ data: [] }))
      setData(Array.isArray(res.data) ? res.data : [])
    } catch (error) {
      setToast({ message: 'Error cargando datos.', tone: 'error' })
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [activeTab, isAuthenticated])

  const handleUpdateArticle = async (id, currentPrice) => {
    const newPrice = prompt('Nuevo precio:', currentPrice)
    if (newPrice === null || newPrice === '') return
    
    try {
      await api.patch(`/api/articulos/${id}`, { precio_base: Number(newPrice) })
      setToast({ message: 'Precio actualizado.', tone: 'success' })
      loadData()
    } catch (error) {
      setToast({ message: 'Error al actualizar precio.', tone: 'error' })
    }
  }

  const handleSetStatus = async (id, newStatus, msg) => {
    if (!confirm(msg)) return
    try {
      await api.patch(`/api/articulos/${id}`, { estado_articulo: newStatus })
      setToast({ message: 'Estado actualizado.', tone: 'success' })
      loadData()
    } catch (error) {
      setToast({ message: 'Error al actualizar estado.', tone: 'error' })
    }
  }

  if (!isAuthenticated) {
    return <div className="container page-section">Debes iniciar sesión para ver tu perfil.</div>
  }

  return (
    <div className="container page-section">
      <div className="card" style={{ marginBottom: '32px', display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div className="brand__logo" style={{ width: '80px', height: '80px', fontSize: '2rem' }}>
          {userEmail?.[0]?.toUpperCase() || 'U'}
        </div>
        <div>
          <h1 style={{ margin: 0 }}>{userEmail}</h1>
          <p className="eyebrow">Miembro desde hoy</p>
        </div>
      </div>

      <div className="tabs">
        <div className={`tab ${activeTab === 'publicados' ? 'tab--active' : ''}`} onClick={() => setActiveTab('publicados')}>
          Mis Artículos
        </div>
        <div className={`tab ${activeTab === 'compras' ? 'tab--active' : ''}`} onClick={() => setActiveTab('compras')}>
          Mis Compras
        </div>
        <div className={`tab ${activeTab === 'favoritos' ? 'tab--active' : ''}`} onClick={() => setActiveTab('favoritos')}>
          Favoritos
        </div>
      </div>

      {loading ? (
        <div className="empty-state">Cargando...</div>
      ) : data.length === 0 ? (
        <div className="empty-state">No hay nada que mostrar aquí todavía.</div>
      ) : (
        <div className="article-grid">
          {activeTab === 'publicados' && data.filter(art => art.estado_articulo !== 'eliminado').map(art => (
            <div key={art.id_articulo} className="card article-card">
              <div className="article-card__content">
                <div className="badges">
                  <span className={`badge ${art.estado_articulo === 'desactivado' ? 'badge--danger' : ''}`}>
                    {art.estado_articulo}
                  </span>
                  <span className="badge badge--category">{art.categoria}</span>
                </div>
                <h3>{art.titulo}</h3>
                <div className="price">€ {Number(art.precio_base).toFixed(2)}</div>
                
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                  {art.estado_articulo === 'disponible' && (
                    <>
                      <button className="button button--secondary" onClick={() => handleUpdateArticle(art.id_articulo, art.precio_base)}>Precio</button>
                      <button className="button button--ghost" style={{ color: 'var(--danger)' }} onClick={() => handleSetStatus(art.id_articulo, 'desactivado', '¿Desactivar artículo?')}>Desactivar</button>
                    </>
                  )}
                  
                  {art.estado_articulo === 'desactivado' && (
                    <>
                      <button className="button button--primary" onClick={() => handleSetStatus(art.id_articulo, 'disponible', '¿Recuperar artículo?')}>Recuperar</button>
                      <button className="button button--ghost" onClick={() => handleSetStatus(art.id_articulo, 'eliminado', '¿Eliminar definitivamente de tu vista?')}>Eliminar</button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {activeTab === 'favoritos' && data.map(art => (
            <ArticleCard 
              key={art.id_articulo} 
              article={art} 
              isFavorite={true} 
              onToggleFav={(id) => setData(prev => prev.filter(a => a.id_articulo !== id))}
            />
          ))}

          {activeTab === 'compras' && data.map(ped => (
            <div key={ped.id_pedido} className="card">
              <strong>Pedido #{ped.id_pedido}</strong>
              <p>Estado: {ped.estado_pedido}</p>
              <p>Total: €{ped.precio_final}</p>
            </div>
          ))}
        </div>
      )}

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
