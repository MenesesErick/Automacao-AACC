import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

// Auth
import LoginPage from '@/pages/auth/LoginPage'

// Aluno
import DashboardAluno from '@/pages/aluno/DashboardAluno'
import EnviarCertificado from '@/pages/aluno/EnviarCertificado'

// Coordenador
import DashboardCoordenador from '@/pages/coordenador/DashboardCoordenador'
import FilaRevisao from '@/pages/coordenador/FilaRevisao'

// Protected Route Component
function RoleRoute({ children, allowedRole }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="min-h-screen bg-bg flex items-center justify-center">Carregando...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== allowedRole) {
    return <Navigate to={`/${user.role}/dashboard`} replace />
  }

  return children
}

export function AppRouter() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="min-h-screen bg-bg flex items-center justify-center">Carregando...</div>
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route 
          path="/login" 
          element={user ? <Navigate to={`/${user.role}/dashboard`} replace /> : <LoginPage />} 
        />

        {/* ALUNO Routes */}
        <Route 
          path="/aluno/dashboard" 
          element={
            <RoleRoute allowedRole="aluno">
              <DashboardAluno />
            </RoleRoute>
          } 
        />
        <Route 
          path="/aluno/enviar" 
          element={
            <RoleRoute allowedRole="aluno">
              <EnviarCertificado />
            </RoleRoute>
          } 
        />
        
        {/* COORDENADOR Routes */}
        <Route 
          path="/coordenador/dashboard" 
          element={
            <RoleRoute allowedRole="coordenador">
              <DashboardCoordenador />
            </RoleRoute>
          } 
        />
        <Route 
          path="/coordenador/revisao" 
          element={
            <RoleRoute allowedRole="coordenador">
              <FilaRevisao />
            </RoleRoute>
          } 
        />

        {/* Root Redirect */}
        <Route 
          path="/" 
          element={<Navigate to={user ? `/${user.role}/dashboard` : "/login"} replace />} 
        />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
