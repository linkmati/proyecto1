export default function ArticleCard({ article, onOffer }) {
  const mainImage = article.fotos?.[0]?.image_url

  return (
    <article className="card article-card">
      <div className="article-card__image-container">
        {mainImage ? (
          <img src={mainImage} alt={article.titulo} className="article-card__image" />
        ) : (
          <div className="article-card__placeholder">Sin imagen</div>
        )}
      </div>

      <div className="article-card__content">
        <div className="article-card__top">
          <div>
            <div className="badges">
              <span className="badge badge--status">{article.estado_articulo || 'disponible'}</span>
              <span className="badge badge--category">{article.categoria}</span>
            </div>
            <h3>{article.titulo}</h3>
          </div>
          <div className="price">€ {Number(article.precio_base).toFixed(2)}</div>
        </div>

        <p className="article-card__description">
          {article.descripcion || 'Sin descripción.'}
        </p>

        <div className="meta-grid">
          <div>
            <span>ID</span>
            <strong>{article.id_articulo}</strong>
          </div>
        </div>

        <button className="button button--primary button--full" onClick={() => onOffer(article)}>
          Hacer oferta
        </button>
      </div>
    </article>
  )
}
