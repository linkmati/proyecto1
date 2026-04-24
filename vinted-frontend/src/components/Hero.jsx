import { Link } from 'react-router-dom'

export default function Hero() {
  return (
    <section className="hero">
      <div className="container hero__grid">
        <div>
          <span className="eyebrow">Marketplace moderno conectado a FastAPI</span>
          <h1>Compra, vende y negocia con una interfaz que sí da gusto abrir.</h1>
          <p>
            Este frontend usa tus endpoints de autenticación, artículos y ofertas.
            Bonito por fuera, útil por dentro. Como debería ser todo software decente.
          </p>
          <div className="hero__actions">
            <Link className="button button--primary" to="/publicar">
              Publicar artículo
            </Link>
            <Link className="button button--secondary" to="/auth">
              Crear cuenta
            </Link>
          </div>
        </div>

        <div className="hero-card">
          <div className="hero-card__row">
            <span className="status-dot"></span>
            <span>Backend conectado a Supabase</span>
          </div>
          <div className="hero-card__stats">
            <article>
              <strong>Auth</strong>
              <span>Registro y login</span>
            </article>
            <article>
              <strong>Artículos</strong>
              <span>Listado y creación</span>
            </article>
            <article>
              <strong>Ofertas</strong>
              <span>Oferta y contraoferta</span>
            </article>
          </div>
        </div>
      </div>
    </section>
  )
}
