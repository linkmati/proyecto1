import { Navigate, Route, Routes } from 'react-router-dom'
import Header from './components/Header'
import HomePage from './pages/HomePage'
import AuthPage from './pages/AuthPage'
import PublishPage from './pages/PublishPage'
import CounterOfferPage from './pages/CounterOfferPage'
import ProfilePage from './pages/ProfilePage'
import MessagesPage from './pages/MessagesPage'
import ArticleDetailPage from './pages/ArticleDetailPage'

export default function App() {
  return (
    <div className="app-shell">
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/publicar" element={<PublishPage />} />
          <Route path="/articulo/:id" element={<ArticleDetailPage />} />
          <Route path="/perfil" element={<ProfilePage />} />
          <Route path="/mensajes" element={<MessagesPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
