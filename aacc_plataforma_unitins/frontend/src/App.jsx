import { AppRouter } from '@/routes'
import { AuthProvider } from '@/contexts/AuthContext'
import { Toaster } from 'sonner'
import '@/styles/globals.css'

export default function App() {
  return (
    <AuthProvider>
      <Toaster richColors position="top-right" />
      <AppRouter />
    </AuthProvider>
  )
}
