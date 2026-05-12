import { useEffect, useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Navigate } from 'react-router-dom'

export default function AdminPage() {
  const { role, token } = useAuth()
  const [activeTab, setActiveTab] = useState('items')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  if (role !== 'admin') {
    return <Navigate to="/" replace />
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      let endpoint = `/api/admin/${activeTab}`
      if (search && (activeTab === 'items' || activeTab === 'users')) {
        endpoint += `?search=${encodeURIComponent(search)}`
      }
      const res = await api.get(endpoint)
      setData(res.data)
    } catch (err) {
      console.error('Error fetching admin data:', err)
      setData([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [activeTab, search])

  const handleDeleteItem = async (id) => {
    if (!window.confirm('¿Seguro que quieres eliminar este artículo?')) return
    try {
      await api.delete(`/api/admin/items/${id}`)
      fetchData()
    } catch (err) {
      alert('Error al eliminar artículo')
    }
  }

  const handleSuspendUser = async (id) => {
    if (!window.confirm('¿Seguro que quieres suspender a este usuario?')) return
    try {
      await api.patch(`/api/admin/users/${id}/suspend`)
      fetchData()
    } catch (err) {
      alert('Error al suspender usuario')
    }
  }

  const handleDeleteOffer = async (id) => {
    if (!window.confirm('¿Seguro que quieres eliminar esta oferta?')) return
    try {
      await api.delete(`/api/admin/offers/${id}`)
      fetchData()
    } catch (err) {
      alert('Error al eliminar oferta')
    }
  }

  return (
    <div className="container" style={{ padding: '2rem 0' }}>
      <h1 className="title">Panel de Administración</h1>

      <nav role="tablist" aria-label="Secciones de administración" style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button 
          role="tab"
          aria-selected={activeTab === 'items'}
          className={`button ${activeTab === 'items' ? 'button--primary' : 'button--ghost'}`}
          onClick={() => { setActiveTab('items'); setSearch(''); }}
        >
          Artículos
        </button>
        <button 
          role="tab"
          aria-selected={activeTab === 'users'}
          className={`button ${activeTab === 'users' ? 'button--primary' : 'button--ghost'}`}
          onClick={() => { setActiveTab('users'); setSearch(''); }}
        >
          Usuarios
        </button>
        <button 
          role="tab"
          aria-selected={activeTab === 'offers'}
          className={`button ${activeTab === 'offers' ? 'button--primary' : 'button--ghost'}`}
          onClick={() => { setActiveTab('offers'); setSearch(''); }}
        >
          Ofertas
        </button>
      </nav>

      {(activeTab === 'items' || activeTab === 'users') && (
        <div style={{ marginBottom: '1rem' }}>
          <input 
            type="text" 
            placeholder={`Buscar ${activeTab === 'items' ? 'artículos...' : 'usuarios...'}`} 
            aria-label={`Filtrar ${activeTab === 'items' ? 'artículos por título' : 'usuarios por email'}`}
            className="input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {loading ? (
        <p role="status">Cargando datos...</p>
      ) : (
        <div style={{ overflowX: 'auto', background: 'white', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <caption style={{ clip: 'rect(0 0 0 0)', clipPath: 'inset(50%)', height: '1px', overflow: 'hidden', position: 'absolute', whiteSpace: 'nowrap', width: '1px' }}>
              Gestión de {activeTab === 'items' ? 'artículos' : activeTab === 'users' ? 'usuarios' : 'ofertas'}
            </caption>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                {activeTab === 'items' && (
                  <>
                    <th scope="col" style={thStyle}>ID</th>
                    <th scope="col" style={thStyle}>Título</th>
                    <th scope="col" style={thStyle}>Precio</th>
                    <th scope="col" style={thStyle}>Estado</th>
                    <th scope="col" style={thStyle}>Vendedor</th>
                    <th scope="col" style={thStyle}>Acciones</th>
                  </>
                )}
                {activeTab === 'users' && (
                  <>
                    <th scope="col" style={thStyle}>ID</th>
                    <th scope="col" style={thStyle}>Email</th>
                    <th scope="col" style={thStyle}>Estado</th>
                    <th scope="col" style={thStyle}>Rol</th>
                    <th scope="col" style={thStyle}>Creado</th>
                    <th scope="col" style={thStyle}>Acciones</th>
                  </>
                )}
                {activeTab === 'offers' && (
                  <>
                    <th scope="col" style={thStyle}>ID</th>
                    <th scope="col" style={thStyle}>Artículo ID</th>
                    <th scope="col" style={thStyle}>Importe</th>
                    <th scope="col" style={thStyle}>Estado</th>
                    <th scope="col" style={thStyle}>Comprador ID</th>
                    <th scope="col" style={thStyle}>Acciones</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.id_articulo || item.id_usuario || item.id_oferta} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  {activeTab === 'items' && (
                    <>
                      <td style={tdStyle}>{item.id_articulo}</td>
                      <td style={tdStyle}>{item.titulo}</td>
                      <td style={tdStyle}>{item.precio_base}€</td>
                      <td style={tdStyle}>{item.estado_articulo}</td>
                      <td style={tdStyle}>{item.id_vendedor}</td>
                      <td style={tdStyle}>
                        <button 
                          className="button button--danger button--small" 
                          aria-label={`Eliminar artículo ${item.titulo}`}
                          onClick={() => handleDeleteItem(item.id_articulo)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </>
                  )}
                  {activeTab === 'users' && (
                    <>
                      <td style={tdStyle}>{item.id_usuario}</td>
                      <td style={tdStyle}>{item.email}</td>
                      <td style={tdStyle}>{item.estado}</td>
                      <td style={tdStyle}>{item.rol}</td>
                      <td style={tdStyle}>{new Date(item.created_at).toLocaleDateString()}</td>
                      <td style={tdStyle}>
                        <button 
                          className="button button--warning button--small" 
                          style={{ marginRight: '0.5rem' }}
                          aria-label={`Suspender usuario ${item.email}`}
                          onClick={() => handleSuspendUser(item.id_usuario)}
                          disabled={item.estado === 'suspendido'}
                        >
                          Suspender
                        </button>
                      </td>
                    </>
                  )}
                  {activeTab === 'offers' && (
                    <>
                      <td style={tdStyle}>{item.id_oferta}</td>
                      <td style={tdStyle}>{item.id_articulo}</td>
                      <td style={tdStyle}>{item.importe}€</td>
                      <td style={tdStyle}>{item.estado}</td>
                      <td style={tdStyle}>{item.id_comprador}</td>
                      <td style={tdStyle}>
                        <button 
                          className="button button--danger button--small" 
                          aria-label={`Eliminar oferta ID ${item.id_oferta}`}
                          onClick={() => handleDeleteOffer(item.id_oferta)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>No se encontraron datos</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const thStyle = {
  textAlign: 'left',
  padding: '1rem',
  fontSize: '0.875rem',
  fontWeight: '600',
  color: '#4b5563'
}

const tdStyle = {
  padding: '1rem',
  fontSize: '0.875rem',
  color: '#1f2937'
}
