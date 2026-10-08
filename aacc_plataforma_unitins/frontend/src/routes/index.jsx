import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

// Auth
import LoginPage from '@/pages/auth/LoginPage'

// Aluno
import DashboardAluno from '@/pages/aluno/DashboardAluno'
import SubmeterCertificado from '@/pages/aluno/SubmeterCertificado'
import HistoricoAluno from '@/pages/aluno/HistoricoAluno'
import VisualizarCertificado from '@/pages/aluno/VisualizarCertificado'

// Coordenador
import DashboardCoordenador from '@/pages/coordenador/DashboardCoordenador'
import FilaRevisao from '@/pages/coordenador/FilaRevisao'
import GestaoAlunos from '@/pages/coordenador/GestaoAlunos'
import AvaliarCertificado from '@/pages/coordenador/AvaliarCertificado'
import DossieAluno from '@/pages/coordenador/DossieAluno'

// Administrador
import AdminDashboard from '@/pages/admin/AdminDashboard'
import AdminCategorias from '@/pages/admin/AdminCategorias'
import AdminCursos from '@/pages/admin/AdminCursos'
import AdminCoordenadores from '@/pages/admin/AdminCoordenadores'

// Shared
import RegrasCategorias from '@/pages/shared/RegrasCategorias'


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
              <SubmeterCertificado />
            </RoleRoute>
          } 
        />
        <Route 
          path="/aluno/historico" 
          element={
            <RoleRoute allowedRole="aluno">
              <HistoricoAluno />
            </RoleRoute>
          } 
        />
        <Route
          path="/aluno/certificados/:id"
          element={
            <RoleRoute allowedRole="aluno">
              <VisualizarCertificado />
            </RoleRoute>
          }
        />
        <Route
          path="/aluno/regras"
          element={
            <RoleRoute allowedRole="aluno">
              <RegrasCategorias />
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
        <Route 
          path="/coordenador/alunos" 
          element={
            <RoleRoute allowedRole="coordenador">
              <GestaoAlunos />
            </RoleRoute>
          } 
        />
        <Route
          path="/coordenador/certificados/:id"
          element={
            <RoleRoute allowedRole="coordenador">
              <AvaliarCertificado />
            </RoleRoute>
          }
        />
        <Route
          path="/coordenador/alunos/:id"
          element={
            <RoleRoute allowedRole="coordenador">
              <DossieAluno />
            </RoleRoute>
          }
        />
        <Route
          path="/coordenador/regras"
          element={
            <RoleRoute allowedRole="coordenador">
              <RegrasCategorias />
            </RoleRoute>
          }
        />

        {/* ADMIN Routes */}
        <Route 
          path="/admin/dashboard" 
          element={
            <RoleRoute allowedRole="admin">
              <AdminDashboard />
            </RoleRoute>
          } 
        />
        <Route 
          path="/admin/categorias" 
          element={
            <RoleRoute allowedRole="admin">
              <AdminCategorias />
            </RoleRoute>
          } 
        />
        <Route 
          path="/admin/cursos" 
          element={
            <RoleRoute allowedRole="admin">
              <AdminCursos />
            </RoleRoute>
          } 
        />
        <Route 
          path="/admin/coordenadores" 
          element={
            <RoleRoute allowedRole="admin">
              <AdminCoordenadores />
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
