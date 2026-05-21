import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

const Hero = () => {
  const navigate = useNavigate();

  return (
    <div className="hero-section">
      <div className="container" style={{ display: 'flex', alignItems: 'center', gap: '40px' }}>
        <motion.div 
          className="hero-content" 
          style={{ flex: 1.2 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="hero-title">
            Vende lo que ya no usas. <span style={{ color: 'var(--primary)' }}>Haz espacio para lo nuevo.</span>
          </h1>
          
          <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', marginBottom: '32px', maxWidth: '540px' }}>
            Únete a nuestra comunidad. Vende ropa, accesorios y más de forma sencilla y segura.
          </p>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-primary" onClick={() => navigate('/publicar')} style={{ padding: '14px 28px', fontSize: '1rem', borderRadius: '4px' }}>
              Vender ahora
              <ArrowRight size={18} />
            </button>
            <button className="btn btn-secondary" onClick={() => {
               document.getElementById('items-grid')?.scrollIntoView({ behavior: 'smooth' });
            }} style={{ padding: '14px 28px', fontSize: '1rem', borderRadius: '4px' }}>
              Ver novedades
            </button>
          </div>
        </motion.div>

        <motion.div 
          className="hero-image" 
          style={{ flex: 1, display: 'none', display: 'block' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <img 
            src="https://images.unsplash.com/photo-1558769132-cb1aea458c5e?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" 
            alt="Fashion" 
            style={{ width: '100%', height: '400px', objectFit: 'cover', borderRadius: 'var(--radius-md)' }}
          />
        </motion.div>
      </div>
    </div>
  );
};

export default Hero;
