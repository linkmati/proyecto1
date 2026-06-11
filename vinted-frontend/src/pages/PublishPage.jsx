import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import Toast from '../components/Toast'
import { Upload, X, Package } from 'lucide-react'

export default function PublishPage() {
  const [titulo, setTitulo] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [precio, setPrecio] = useState('')
  const [categoria, setCategory] = useState('Moda')
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const navigate = useNavigate()
  const CATEGORIAS = ['Moda', 'Hogar', 'Electrónica', 'Entretenimiento', 'Otros']

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files)
    setImages(prev => [...prev, ...files])
  }

  const removeImage = (index) => {
    setImages(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      // 1. Primero creamos el artículo en la base de datos
      const itemRes = await api.post('/api/items', {
        titulo,
        descripcion,
        precio_base: parseFloat(precio),
        categoria,
        estado_articulo: 'disponible'
      })

      const itemId = itemRes.data.id_articulo

      // 2. Después subimos todas las fotos que haya seleccionado el usuario
      for (const img of images) {
        const formData = new FormData()
        formData.append('file', img)
        await api.post(`/api/items/${itemId}/images`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }

      setToast({ message: '¡Artículo publicado con éxito!', tone: 'success' })
      // Esperamos un poco para que el usuario vea el mensaje y nos vamos a la home
      setTimeout(() => navigate('/'), 1500)
    } catch (error) {
      setToast({ message: 'Error al publicar el artículo.', tone: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container" style={{ padding: '40px 0', maxWidth: '800px' }}>
      <div className="card" style={{ padding: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
          <div style={{ background: 'var(--primary-soft)', color: 'var(--primary)', padding: '12px', borderRadius: '12px' }}>
            <Package size={32} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.8rem' }}>Vende un artículo</h1>
            <p style={{ color: 'var(--text-soft)' }}>Sube fotos y describe tu tesoro</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="form">
          {/* Images */}
          <div style={{ marginBottom: '24px' }}>
            <label>Fotos (máx. 5)</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '12px', marginTop: '8px' }}>
              {images.map((img, idx) => (
                <div key={idx} style={{ position: 'relative', aspectRatio: '1', border: '1px solid var(--line)', borderRadius: '8px', overflow: 'hidden' }}>
                  <img src={URL.createObjectURL(img)} alt="preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <button type="button" onClick={() => removeImage(idx)} style={{ position: 'absolute', top: '4px', right: '4px', background: 'rgba(0,0,0,0.5)', color: 'white', border: 'none', borderRadius: '50%', padding: '4px', cursor: 'pointer' }}>
                    <X size={14} />
                  </button>
                </div>
              ))}
              {images.length < 5 && (
                <label style={{ aspectRatio: '1', border: '2px dashed var(--line)', borderRadius: '8px', display: 'grid', placeItems: 'center', cursor: 'pointer', margin: 0 }}>
                  <input type="file" hidden multiple accept="image/*" onChange={handleImageChange} />
                  <div style={{ textAlign: 'center', color: 'var(--text-soft)' }}>
                    <Upload size={24} style={{ margin: '0 auto 4px' }} />
                    <span style={{ fontSize: '0.8rem' }}>Añadir foto</span>
                  </div>
                </label>
              )}
            </div>
          </div>

          <div>
            <label>Título</label>
            <input type="text" required className="search-input" style={{ paddingLeft: '16px' }} placeholder="p. ej. Camiseta vintage de seda" value={titulo} onChange={(e) => setTitulo(e.target.value)} />
          </div>

          <div>
            <label>Describe tu artículo</label>
            <textarea required className="search-input" style={{ paddingLeft: '16px', minHeight: '120px', resize: 'vertical' }} placeholder="Indica el estado, la talla, etc." value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label>Categoría</label>
              <select className="search-input" style={{ paddingLeft: '12px' }} value={categoria} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label>Precio (€)</label>
              <input type="number" required step="0.01" className="search-input" style={{ paddingLeft: '16px' }} placeholder="0.00" value={precio} onChange={(e) => setPrecio(e.target.value)} />
            </div>
          </div>

          <div style={{ marginTop: '32px', borderTop: '1px solid var(--line)', paddingTop: '24px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button type="button" className="btn btn-ghost" onClick={() => navigate(-1)}>Cancelar</button>
            <button type="submit" className="btn btn-primary" style={{ padding: '12px 40px', borderRadius: '4px' }} disabled={loading}>
              {loading ? 'Publicando...' : 'Publicar ahora'}
            </button>
          </div>
        </form>
      </div>

      <Toast message={toast.message} tone={toast.tone} onClose={() => setToast({ message: '', tone: 'success' })} />
    </div>
  )
}
