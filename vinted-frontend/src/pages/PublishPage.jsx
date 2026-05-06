import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import Toast from '../components/Toast'

const CATEGORIAS = ['Moda', 'Hogar', 'Electrónica', 'Entretenimiento', 'Otros']

export default function PublishPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    titulo: '',
    descripcion: '',
    precio_base: '',
    categoria: 'Moda',
  })
  const [files, setFiles] = useState([])
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })
  const onFileChange = (e) => setFiles(Array.from(e.target.files))

  const onSubmit = async (e) => {
    e.preventDefault()
    if (loading) return

    try {
      setLoading(true)
      
      // 1. Create Article (Item)
      const response = await api.post('/api/items', {
        ...form,
        precio_base: Number(form.precio_base),
      })
      
      const idArticulo = response.data.id_articulo
      
      // 2. Upload Images
      if (files.length > 0) {
        for (const file of files) {
          const formData = new FormData()
          formData.append('file', file)
          await api.post(`/api/items/${idArticulo}/images`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
        }
      }

      setToast({
        message: `Artículo creado correctamente con ${files.length} imágenes.`,
        tone: 'success',
      })
      setForm({ titulo: '', descripcion: '', precio_base: '', categoria: 'Moda' })
      setFiles([])
    } catch (error) {
      setToast({
        message: error.response?.data?.detail || 'No se pudo publicar el artículo.',
        tone: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="container page-section publish-layout">
      <div className="card spotlight-card">
        <span className="eyebrow">Nuevo artículo</span>
        <h1>Publica algo que valga la pena vender</h1>
        <p>
          Conectado a <code>/api/items</code> y <code>/api/items/id/images</code>.
          ¡Ahora con categorías y fotos!
        </p>
      </div>

      <div className="card">
        <form className="form" onSubmit={onSubmit}>
          <label>
            Título
            <input
              name="titulo"
              value={form.titulo}
              onChange={onChange}
              placeholder="Ejemplo: Sudadera vintage azul"
              required
            />
          </label>

          <label>
            Categoría
            <select name="categoria" value={form.categoria} onChange={onChange} required>
              {CATEGORIAS.map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </label>

          <label>
            Descripción
            <textarea
              name="descripcion"
              rows="4"
              value={form.descripcion}
              onChange={onChange}
              placeholder="Cuenta lo importante..."
            />
          </label>

          <label>
            Precio base
            <input
              type="number"
              name="precio_base"
              min="0"
              step="0.01"
              value={form.precio_base}
              onChange={onChange}
              placeholder="49.99"
              required
            />
          </label>

          <label>
            Fotos
            <input 
              type="file" 
              multiple 
              accept="image/*" 
              onChange={onFileChange}
            />
            {files.length > 0 && <small>{files.length} archivos seleccionados</small>}
          </label>

          <button className="button button--primary button--full" disabled={loading}>
            {loading ? 'Publicando...' : 'Publicar artículo'}
          </button>
        </form>
      </div>

      <Toast
        message={toast.message}
        tone={toast.tone}
        onClose={() => setToast({ message: '', tone: 'success' })}
      />
    </section>
  )
}
