import { Navigate, Route, Routes } from 'react-router-dom'
import { useState } from 'react'
import Header from './components/Header'
import HomePage from './pages/HomePage'
import AuthPage from './pages/AuthPage'
import PublishPage from './pages/PublishPage'
import CounterOfferPage from './pages/CounterOfferPage'
import ProfilePage from './pages/ProfilePage'
import MessagesPage from './pages/MessagesPage'
import ArticleDetailPage from './pages/ArticleDetailPage'
import AdminPage from './pages/AdminPage'

export default function App() {
  const [globalSearch, setGlobalSearch] = useState('')

  return (
    <div className="app-shell">
      <Header onSearch={setGlobalSearch} />
      <main>
        <Routes>
          <Route path="/" element={<HomePage searchTerm={globalSearch} />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/publicar" element={<PublishPage />} />
          <Route path="/articulo/:id" element={<ArticleDetailPage />} />
          <Route path="/perfil" element={<ProfilePage />} />
          <Route path="/mensajes" element={<MessagesPage />} />
          <Route path="/contraoferta/:id" element={<CounterOfferPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
