import { AppRouter } from '@/routes'
import { AuthProvider } from '@/contexts/AuthContext'
import '@/styles/globals.css'

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  )
}
