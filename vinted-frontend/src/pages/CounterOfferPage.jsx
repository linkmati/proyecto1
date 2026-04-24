import { useState } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import Toast from '../components/Toast'

export default function CounterOfferPage() {
  const { isAuthenticated } = useAuth()
  const [form, setForm] = useState({ id_oferta: '', nuevo_importe: '', mensaje: '' })
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState({ message: '', tone: 'success' })

  const onChange = (e) => {
    setForm((current) => ({ ...current, [e.target.name]: e.target.value }))
  }

  const onSubmit = async (e) => {
    e.preventDefault()

    if (!isAuthenticated) {
      setToast({ message: 'Debes iniciar sesión para contraofertar.', tone: 'error' })
      return
    }

    try {
      setLoading(true)
      await api.patch(`/api/ofertas/${form.id_oferta}/contraoferta`, {
        nuevo_importe: Number(form.nuevo_importe),
        mensaje: form.mensaje,
      })
      setToast({ message: 'Contraoferta enviada correctamente.', tone: 'success' })
      setForm({ id_oferta: '', nuevo_importe: '', mensaje: '' })
    } catch (error) {
      setToast({
        message: error.response?.data?.detail || 'No se pudo enviar la contraoferta.',
        tone: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="container page-section publish-layout">
      <div className="card spotlight-card">
        <span className="eyebrow">Negociación</span>
        <h1>Enviar contraoferta</h1>
        <p>
          Tu backend actual no tiene un endpoint para listar ofertas, así que aquí dejé
          un panel funcional para contraofertar usando el <strong>ID de oferta</strong>
          que devuelve el backend al crearla.
        </p>
      </div>

      <div className="card">
        <form className="form" onSubmit={onSubmit}>
          <label>
            ID de la oferta
            <input
              name="id_oferta"
              value={form.id_oferta}
              onChange={onChange}
              placeholder="Pega aquí el ID de la oferta"
              required
            />
          </label>

          <label>
            Nuevo importe
            <input
              type="number"
              name="nuevo_importe"
              min="0"
              step="0.01"
              value={form.nuevo_importe}
              onChange={onChange}
              required
            />
          </label>

          <label>
            Nuevo mensaje
            <textarea
              name="mensaje"
              rows="4"
              value={form.mensaje}
              onChange={onChange}
              placeholder="Ejemplo: Te lo dejo a este precio si cerramos hoy"
            />
          </label>

          <button className="button button--primary button--full" disabled={loading}>
            {loading ? 'Enviando...' : 'Enviar contraoferta'}
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
