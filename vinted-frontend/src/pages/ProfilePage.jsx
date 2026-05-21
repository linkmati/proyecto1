import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import ArticleCard from '../components/ArticleCard'
import Toast from '../components/Toast'
import { motion, AnimatePresence } from 'framer-motion'
import { User, Settings, Heart, Package, Edit3, Trash2, Eye, EyeOff, Save, X, ShoppingBag, CheckCircle } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('for_sale') // 'for_sale', 'sold', 'purchased', 'favorites'
  const [items, setItems] = useState([])
  const [favoritesIds, setFavoritesIds] = useState([]) 
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  // Editing state
  const [editingItem, setEditingItem] = useState(null)
  const [editPrice, setEditPrice] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      let endpoint = ''
      
      switch (activeTab) {
        case 'for_sale':
          // We can reuse get_my_items and filter for 'disponible' on frontend or add params
          const resSale = await api.get('/api/users/me/items')
          setItems((resSale.data || []).filter(i => i.estado_articulo === 'disponible' || i.estado_articulo === 'desactivado'))
          break
        case 'sold':
          const resSold = await api.get('/api/users/me/items')
          setItems((resSold.data || []).filter(i => i.estado_articulo === 'vendido'))
          break
        case 'purchased':
          // Purchased needs to fetch from the orders endpoint but we want full items
          // For now we'll call a placeholder or filter if orders include item data
          const resPurchased = await api.get('/api/users/me/purchases')
          // Since purchases usually returns orders, we might need a better endpoint
          // but for this MVP we'll show them as cards if data permits
          setItems(resPurchased.data || []) 
          break
        case 'favorites':
          const resFavs = await api.get('/api/users/me/favorites')
          setItems(resFavs.data || [])
          break
        default:
          break
      }

      // Sync heart states
      const favsRes = await api.get('/api/favorites')
      setFavoritesIds((favsRes.data || []).map(f => String(f.id_articulo)))
      
    } catch (error) {
      setToast({ message: 'Error al cargar los datos del perfil.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [activeTab])

  const toggleFavorite = async (id) => {
    const idStr = String(id)
    try {
      await api.delete(`/api/favorites/${id}`)
      setFavoritesIds(prev => prev.filter(f => f !== idStr))
      if (activeTab === 'favorites') {
        setItems(prev => prev.filter(item => String(item.id_articulo) !== idStr))
      }
      setToast({ message: 'Eliminado de favoritos', tone: 'success' })
    } catch (e) {
      setToast({ message: 'Error al quitar de favoritos', tone: 'error' })
    }
  }

  const handleUpdatePrice = async (item) => {
    try {
      const newPrice = parseFloat(editPrice)
      if (isNaN(newPrice) || newPrice <= 0) {
        setToast({ message: 'Precio no válido.', tone: 'error' })
        return
      }
      await api.patch(`/api/items/${item.id_articulo}`, { precio_base: newPrice })
      setToast({ message: 'Precio actualizado con éxito.', tone: 'success' })
      setEditingItem(null)
      loadData()
    } catch (e) {
      setToast({ message: 'Error al actualizar el precio.', tone: 'error' })
    }
  }

  const handleToggleStatus = async (item) => {
    const isDeactivated = item.estado_articulo === 'desactivado'
    const newStatus = isDeactivated ? 'disponible' : 'desactivado'
    const confirmMsg = isDeactivated 
      ? '¿Quieres volver a poner a la venta este artículo?' 
      : '¿Quieres quitar este artículo de la venta temporalmente?'

    if (!window.confirm(confirmMsg)) return

    try {
      await api.patch(`/api/items/${item.id_articulo}`, { estado_articulo: newStatus })
      setToast({ message: isDeactivated ? 'Artículo a la venta.' : 'Artículo ocultado.', tone: 'success' })
      loadData()
    } catch (e) {
      setToast({ message: 'Error al cambiar el estado del artículo.', tone: 'error' })
    }
  }

  const handleDeleteItem = async (item) => {
    if (!window.confirm('¿Estás seguro de eliminar este artículo permanentemente? Esta acción no se puede deshacer.')) return
    try {
      await api.delete(`/api/items/${item.id_articulo}`)
      setToast({ message: 'Artículo eliminado.', tone: 'success' })
      loadData()
    } catch (e) {
      setToast({ message: 'Error al eliminar el artículo.', tone: 'error' })
    }
  }

  return (
    <div className="container" style={{ padding: '40px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px', marginBottom: '48px' }}>
        <div style={{ width: '100px', height: '100px', borderRadius: '50%', background: 'var(--primary-soft)', color: 'var(--primary)', display: 'grid', placeItems: 'center' }}>
          <User size={48} />
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '4px' }}>{user?.nombre_usuario || 'Usuario'}</h1>
          <p style={{ color: 'var(--text-soft)' }}>{user?.email}</p>
        </div>
      </div>

      <div className="tabs" style={{ marginBottom: '32px', borderBottom: '1px solid var(--line)', display: 'flex', gap: '24px', overflowX: 'auto', paddingBottom: '2px' }}>
        <TabButton label="En venta" icon={<Package size={20}/>} active={activeTab === 'for_sale'} onClick={() => setActiveTab('for_sale')} />
        <TabButton label="Vendidos" icon={<CheckCircle size={20}/>} active={activeTab === 'sold'} onClick={() => setActiveTab('sold')} />
        <TabButton label="Comprados" icon={<ShoppingBag size={20}/>} active={activeTab === 'purchased'} onClick={() => setActiveTab('purchased')} />
        <TabButton label="Favoritos" icon={<Heart size={20}/>} active={activeTab === 'favorites'} onClick={() => setActiveTab('favorites')} />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px' }}>Cargando...</div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px', color: 'var(--text-soft)', background: 'var(--bg-soft)', borderRadius: 'var(--radius-lg)' }}>
          <p>No hay artículos en esta sección.</p>
        </div>
      ) : (
        <div className="article-grid">
          {items.map(item => {
             // For purchased tab, 'item' might be an order object, let's normalize
             const articleData = activeTab === 'purchased' ? item.articulo : item;
             if (!articleData) return null;

             return (
              <div key={articleData.id_articulo || item.id_pedido} style={{ position: 'relative' }}>
                <ArticleCard 
                  article={articleData} 
                  isFavorite={favoritesIds.includes(String(articleData.id_articulo))} 
                  onToggleFavorite={toggleFavorite}
                />
                
                {/* Management Overlay for OWN active items */}
                {activeTab === 'for_sale' && (
                  <div style={{ 
                    marginTop: '12px', 
                    display: 'flex', 
                    gap: '8px', 
                    padding: '12px', 
                    background: 'var(--bg-soft)', 
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--line)'
                  }}>
                    {editingItem === articleData.id_articulo ? (
                      <div style={{ display: 'flex', gap: '4px', width: '100%' }}>
                        <input 
                          autoFocus
                          type="number"
                          className="search-input"
                          style={{ height: '36px', flex: 1, padding: '0 8px' }}
                          value={editPrice}
                          onChange={(e) => setEditPrice(e.target.value)}
                        />
                        <button className="btn btn-primary" style={{ padding: '8px' }} onClick={() => handleUpdatePrice(articleData)}>
                          <Save size={16} />
                        </button>
                        <button className="btn btn-ghost" style={{ padding: '8px' }} onClick={() => setEditingItem(null)}>
                          <X size={16} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <button 
                          className="btn btn-ghost" 
                          style={{ flex: 1, fontSize: '0.8rem', gap: '4px', padding: '8px' }}
                          onClick={() => {
                            setEditingItem(articleData.id_articulo)
                            setEditPrice(articleData.precio_base)
                          }}
                        >
                          <Edit3 size={14} /> Precio
                        </button>
                        <button 
                          className="btn btn-ghost" 
                          style={{ padding: '8px' }}
                          onClick={() => handleToggleStatus(articleData)}
                          title={articleData.estado_articulo === 'desactivado' ? 'Poner a la venta' : 'Ocultar artículo'}
                        >
                          {articleData.estado_articulo === 'desactivado' ? <Eye size={18} color="var(--primary)" /> : <EyeOff size={18} />}
                        </button>
                        <button 
                          className="btn btn-ghost" 
                          style={{ padding: '8px', color: '#ef4444' }}
                          onClick={() => handleDeleteItem(articleData)}
                        >
                          <Trash2 size={18} />
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Badge for sold items in other tabs */}
                {articleData.estado_articulo === 'vendido' && activeTab !== 'purchased' && (
                  <div style={{ position: 'absolute', top: '10px', left: '10px', background: '#ef4444', color: 'white', padding: '4px 12px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                    VENDIDO
                  </div>
                )}
              </div>
             )
          })}
        </div>
      )}

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}

function TabButton({ label, icon, active, onClick }) {
  return (
    <button 
      className={`btn btn-ghost ${active ? 'active' : ''}`} 
      style={{ 
        borderRadius: 0, 
        padding: '12px 4px', 
        borderBottom: active ? '2px solid var(--primary)' : '2px solid transparent',
        color: active ? 'var(--primary)' : 'var(--text-soft)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        whiteSpace: 'nowrap'
      }}
      onClick={onClick}
    >
      {icon}
      <span style={{ fontWeight: active ? '700' : '500' }}>{label}</span>
    </button>
  )
}
