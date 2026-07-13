import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage     from '@/pages/auth/LoginPage'
import DashboardPage from '@/pages/dashboard/DashboardPage'

// TODO: importar páginas futuras aqui

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth */}
        <Route path="/login"     element={<LoginPage />} />

        {/* App */}
        <Route path="/dashboard" element={<DashboardPage />} />

        {/* Redirect raiz */}
        <Route path="/"   element={<Navigate to="/dashboard" replace />} />
        <Route path="*"   element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
