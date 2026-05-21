import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, LogOut, Plus, Mail, ShieldAlert } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';

const Header = ({ onSearch }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadMessages, setUnreadMessages] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (user) {
      const fetchUnread = async () => {
        try {
          const res = await api.get('/api/messages/unread-count');
          setUnreadMessages(res.data.count);
        } catch (e) {}
      };
      fetchUnread();
    }
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleSearch = (e) => {
    const value = e.target.value;
    setSearchTerm(value);
    if (onSearch) {
      onSearch(value);
    }
  };

  return (
    <header className="site-header">
      <div className="container header-inner">
        <Link to="/" className="logo">
          <div className="logo-icon" />
          <span>Mas Tienda</span>
        </Link>

        <div className="search-container">
          <Search className="search-icon" size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-soft)' }} />
          <input 
            type="text" 
            placeholder="Buscar artículos..." 
            className="search-input"
            value={searchTerm}
            onChange={handleSearch}
          />
        </div>

        <nav className="header-actions" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {user ? (
            <>
              {/* Admin Access - Only visible to admins */}
              {user.rol === 'admin' && (
                <Link to="/admin" className="btn btn-secondary" style={{ color: '#ef4444', borderColor: '#fee2e2', background: '#fef2f2' }}>
                  <ShieldAlert size={18} />
                  <span>Admin</span>
                </Link>
              )}

              <Link to="/publicar" className="btn btn-primary" style={{ padding: '8px 16px', borderRadius: '4px' }}>
                <Plus size={18} />
                <span>Vender</span>
              </Link>
              
              <Link to="/mensajes" className="btn btn-ghost" style={{ position: 'relative' }}>
                <Mail size={20} />
                {unreadMessages > 0 && (
                  <span style={{ position: 'absolute', top: '8px', right: '12px', background: '#ef4444', width: '8px', height: '8px', borderRadius: '50%' }} />
                )}
              </Link>

              <Link to="/perfil" className="btn btn-ghost" style={{ display: 'flex', gap: '8px', padding: '8px' }}>
                <User size={20} />
                <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>{user.nombre_usuario || 'Perfil'}</span>
              </Link>

              <button onClick={handleLogout} className="btn btn-ghost" title="Cerrar sesión">
                <LogOut size={20} />
              </button>
            </>
          ) : (
            <>
              <Link to="/auth" className="btn btn-ghost">Iniciar sesión</Link>
              <Link to="/auth?mode=register" className="btn btn-primary" style={{ borderRadius: '4px' }}>Regístrate</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

export default Header;
