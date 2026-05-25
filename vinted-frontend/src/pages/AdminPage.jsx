import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Users, Package, Tag, Trash2, CheckCircle, XCircle, AlertTriangle, RefreshCw } from 'lucide-react'

export default function AdminPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('users')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    try {
      setLoading(true)
      const res = await api.get(`/api/admin/${activeTab}`)
      setData(res.data)
    } catch (e) {
      setToast({ message: 'Error al cargar datos de administración.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!id) {
      setToast({ message: 'ID no válido para eliminar.', tone: 'error' })
      return
    }

    if (!window.confirm('¿Estás seguro de eliminar este registro permanentemente?')) return
    
    try {
      await api.delete(`/api/admin/${activeTab}/${id}`)
      setToast({ message: 'Registro eliminado con éxito.', tone: 'success' })
      // Recargar datos
      loadData()
    } catch (e) {
      const errorMsg = e.response?.data?.detail || 'Error al eliminar el registro. Puede que tenga datos vinculados.'
      setToast({ message: errorMsg, tone: 'error' })
    }
  }

  const handleStatusToggle = async (userItem) => {
    const isSuspended = userItem.estado === 'suspendido'
    const action = isSuspended ? 'reactivate' : 'suspend'
    const actionName = isSuspended ? 'reactivar' : 'suspender'
    
    if (!window.confirm(`¿Quieres ${actionName} la cuenta de ${userItem.nombre_usuario}?`)) return
    
    try {
      await api.patch(`/api/admin/users/${userItem.id_usuario}/${action}`)
      setToast({ message: `Usuario ${isSuspended ? 'reactivado' : 'suspendido'} con éxito`, tone: 'success' })
      loadData()
    } catch (e) {
      setToast({ message: 'Error al cambiar el estado del usuario', tone: 'error' })
    }
  }

  const handleCategoryChange = async (itemId, currentCategory) => {
    const CATEGORIAS = ['Moda', 'Hogar', 'Electrónica', 'Entretenimiento', 'Otros']
    const newCategory = window.prompt(`Cambiar categoría (Actual: ${currentCategory}).\nOpciones: ${CATEGORIAS.join(', ')}`, currentCategory)
    
    if (newCategory && CATEGORIAS.includes(newCategory) && newCategory !== currentCategory) {
      try {
        await api.patch(`/api/admin/items/${itemId}/category`, { categoria: newCategory })
        setToast({ message: 'Categoría actualizada con éxito', tone: 'success' })
        loadData()
      } catch (e) {
        setToast({ message: 'Error al actualizar la categoría', tone: 'error' })
      }
    } else if (newCategory && !CATEGORIAS.includes(newCategory)) {
      alert('Categoría no válida. Debe ser una de: ' + CATEGORIAS.join(', '))
    }
  }

  if (user?.rol !== 'admin') {
    return (
      <div className="container" style={{ padding: '100px 0', textAlign: 'center' }}>
        <AlertTriangle size={64} color="#ef4444" style={{ marginBottom: '24px' }} />
        <h1>Acceso Denegado</h1>
        <p>No tienes permisos para ver esta página.</p>
      </div>
    )
  }

  return (
    <div className="container" style={{ padding: '40px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '40px' }}>
        <div style={{ background: 'var(--primary)', color: 'white', padding: '12px', borderRadius: '12px' }}>
          <Shield size={32} />
        </div>
        <div>
          <h1 style={{ fontSize: '2rem' }}>Panel de Administración</h1>
          <p style={{ color: 'var(--text-soft)' }}>Gestión global de la plataforma</p>
        </div>
      </div>

      <div className="tabs" style={{ display: 'flex', gap: '8px', marginBottom: '32px', background: 'var(--bg-soft)', padding: '6px', borderRadius: '8px', width: 'fit-content' }}>
        <button 
          className={`btn ${activeTab === 'users' ? 'btn-primary' : 'btn-ghost'}`} 
          style={{ borderRadius: '6px' }}
          onClick={() => setActiveTab('users')}
        >
          <Users size={18} /> Usuarios
        </button>
        <button 
          className={`btn ${activeTab === 'items' ? 'btn-primary' : 'btn-ghost'}`} 
          style={{ borderRadius: '6px' }}
          onClick={() => setActiveTab('items')}
        >
          <Package size={18} /> Artículos
        </button>
        <button 
          className={`btn ${activeTab === 'offers' ? 'btn-primary' : 'btn-ghost'}`} 
          style={{ borderRadius: '6px' }}
          onClick={() => setActiveTab('offers')}
        >
          <Tag size={18} /> Ofertas
        </button>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead style={{ background: 'var(--bg-soft)', borderBottom: '1px solid var(--line)' }}>
            <tr>
              {activeTab === 'users' && (
                <>
                  <th style={{ padding: '16px 24px' }}>Usuario</th>
                  <th style={{ padding: '16px 24px' }}>Email</th>
                  <th style={{ padding: '16px 24px' }}>Estado</th>
                  <th style={{ padding: '16px 24px' }}>Rol</th>
                  <th style={{ padding: '16px 24px' }}>Acciones</th>
                </>
              )}
              {activeTab === 'items' && (
                <>
                  <th style={{ padding: '16px 24px' }}>Título</th>
                  <th style={{ padding: '16px 24px' }}>Categoría</th>
                  <th style={{ padding: '16px 24px' }}>Precio</th>
                  <th style={{ padding: '16px 24px' }}>Vendedor</th>
                  <th style={{ padding: '16px 24px' }}>Acciones</th>
                </>
              )}
              {activeTab === 'offers' && (
                <>
                  <th style={{ padding: '16px 24px' }}>Articulo</th>
                  <th style={{ padding: '16px 24px' }}>Oferta</th>
                  <th style={{ padding: '16px 24px' }}>Estado</th>
                  <th style={{ padding: '16px 24px' }}>Acciones</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="5" style={{ padding: '40px', textAlign: 'center' }}>Cargando...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan="5" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-soft)' }}>No hay datos disponibles.</td></tr>
            ) : (
              data.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--line)' }}>
                  {activeTab === 'users' && (
                    <>
                      <td style={{ padding: '16px 24px', fontWeight: '600' }}>{item.nombre_usuario}</td>
                      <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>{item.email}</td>
                      <td style={{ padding: '16px 24px' }}>
                        <span className="badge" style={{ 
                          background: item.estado === 'suspendido' ? '#FEE2E2' : '#DCFCE7', 
                          color: item.estado === 'suspendido' ? '#EF4444' : '#166534' 
                        }}>
                          {item.estado}
                        </span>
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <span className="badge" style={{ background: item.rol === 'admin' ? 'var(--primary-soft)' : 'var(--bg-soft)', color: item.rol === 'admin' ? 'var(--primary)' : 'var(--text-soft)' }}>
                          {item.rol}
                        </span>
                      </td>
                      <td style={{ padding: '16px 24px', display: 'flex', gap: '8px' }}>
                        {item.estado === 'suspendido' ? (
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '8px 12px', fontSize: '0.8rem', color: '#166534', borderColor: '#166534' }} 
                            onClick={() => handleStatusToggle(item)}
                          >
                            <CheckCircle size={16} /> Reactivar
                          </button>
                        ) : (
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '8px 12px', fontSize: '0.8rem', color: '#EF4444', borderColor: '#EF4444' }} 
                            onClick={() => handleStatusToggle(item)}
                          >
                            <XCircle size={16} /> Suspender
                          </button>
                        )}
                        <button className="btn btn-ghost" style={{ padding: '8px', color: 'var(--text-soft)' }} onClick={() => handleDelete(item.id_usuario)}>
                          <Trash2 size={16} />
                        </button>
                      </td >
                    </>
                  )}
                  {activeTab === 'items' && (
                    <>
                      <td style={{ padding: '16px 24px', fontWeight: '600' }}>{item.titulo}</td>
                      <td style={{ padding: '16px 24px' }}>
                        <button 
                          className="btn btn-ghost" 
                          style={{ padding: '4px 8px', fontSize: '0.8rem', gap: '4px' }}
                          onClick={() => handleCategoryChange(item.id_articulo, item.categoria)}
                        >
                          <Tag size={14} /> {item.categoria}
                        </button>
                      </td>
                      <td style={{ padding: '16px 24px' }}>{item.precio_base || item.precio} €</td>
                      <td style={{ padding: '16px 24px', color: 'var(--text-muted)' }}>{item.vendedor_nombre}</td>
                      <td style={{ padding: '16px 24px' }}>
                        <button className="btn btn-ghost" style={{ padding: '8px', color: '#ef4444' }} onClick={() => handleDelete(item.id_articulo)}>
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </>
                  )}
                  {activeTab === 'offers' && (
                    <>
                      <td style={{ padding: '16px 24px', fontWeight: '600' }}>{item.articulo_titulo || 'Articulo'}</td>
                      <td style={{ padding: '16px 24px' }}>{item.importe} €</td>
                      <td style={{ padding: '16px 24px' }}>
                        <span className="badge" style={{ background: 'var(--bg-soft)' }}>{item.estado}</span>
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <button className="btn btn-ghost" style={{ padding: '8px', color: '#ef4444' }} onClick={() => handleDelete(item.id_oferta)}>
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
