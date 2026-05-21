import React from 'react';
import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { motion } from 'framer-motion';

const ArticleCard = ({ article, isFavorite, onToggleFavorite }) => {
  return (
    <motion.div 
      className="article-card"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <Link to={`/articulo/${article.id_articulo}`} className="card-link">
        <div className="card-image-wrap">
          <img 
            src={article.fotos?.[0]?.image_url || 'https://via.placeholder.com/300x300?text=Sin+Imagen'} 
            alt={article.titulo} 
            className="card-image"
          />
          <button 
            className={`fav-btn ${isFavorite ? 'active' : ''}`}
            onClick={(e) => {
              e.preventDefault();
              onToggleFavorite(article.id_articulo);
            }}
          >
            <Heart size={18} fill={isFavorite ? 'currentColor' : 'none'} />
          </button>
        </div>
        
        <div className="card-content">
          <div className="card-price">{article.precio_base || article.precio} €</div>
          <div className="card-title">{article.titulo}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-soft)', marginTop: '4px' }}>
            {article.categoria}
          </div>
        </div>
      </Link>
    </motion.div>
  );
};

export default ArticleCard;
