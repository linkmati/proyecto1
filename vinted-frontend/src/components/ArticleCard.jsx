import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function ArticleCard({ article, onOffer, isFavorite, onToggleFav }) {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const mainImage = article.fotos?.[0]?.image_url

  // Usamos un estado local para que el cambio visual sea INSTANTÁNEO
  const [localFav, setLocalFav] = useState(isFavorite)

  // Sincronizar el estado local cuando cambie la prop
  useEffect(() => {
    setLocalFav(isFavorite)
  }, [isFavorite])

  const handleToggleFav = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!isAuthenticated) {
      navigate('/auth')
      return
    }
    
    const targetId = article.id_articulo
    const wasFav = localFav
    
    // 1. Cambio visual optimista (inmediato)
    setLocalFav(!wasFav)
    
    try {
      if (wasFav) {
        console.log('Quitando de favoritos ID:', targetId)
        await api.delete(`/api/favoritos/${targetId}`)
        if (onToggleFav) onToggleFav(targetId, false)
      } else {
        console.log('Añadiendo a favoritos ID:', targetId)
        await api.post(`/api/favoritos/${targetId}`)
        if (onToggleFav) onToggleFav(targetId, true)
      }
    } catch (error) {
      console.error('Error al actualizar favoritos en el servidor:', error)
      // Si falla, revertimos el cambio visual
      setLocalFav(wasFav)
    }
  }

  const goToDetail = () => {
    navigate(`/articulo/${article.id_articulo}`)
  }

  return (
    <article className="card article-card" onClick={goToDetail} style={{ cursor: 'pointer' }}>
      <div className="article-card__image-container" style={{ position: 'relative' }}>
        {mainImage ? (
          <img src={mainImage} alt={article.titulo} className="article-card__image" />
        ) : (
          <div className="article-card__placeholder" style={{ display: 'grid', placeItems: 'center', height: '100%', background: 'var(--bg-soft)' }}>
            Sin imagen
          </div>
        )}
        
        {isAuthenticated && (
          <button 
            className="fav-btn" 
            onClick={handleToggleFav} 
            type="button"
            style={{ 
              position: 'absolute',
              top: '10px',
              right: '10px',
              background: 'white',
              borderRadius: '50%',
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow)',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1.2rem',
              color: localFav ? '#ef4444' : '#a3a3a3',
              zIndex: 10
            }}
          >
            {localFav ? '❤️' : '🤍'}
          </button>
        )}
      </div>

      <div className="article-card__content">
        <div className="badges">
          <span className="badge">{article.estado_articulo}</span>
          <span className="badge badge--category">{article.categoria}</span>
        </div>
        
        <h3 style={{ fontSize: '1rem', margin: '8px 0', fontWeight: '600' }}>{article.titulo}</h3>
        <div className="price" style={{ color: 'var(--primary)', fontWeight: '700' }}>
          € {Number(article.precio_base).toFixed(2)}
        </div>

        <button 
          className="button button--primary button--full" 
          style={{ marginTop: '12px' }}
          onClick={(e) => {
            e.stopPropagation()
            onOffer(article)
          }}
        >
          Hacer oferta
        </button>
      </div>
    </article>
  )
}
