import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GraduationCap, Users, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/atoms/Button'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [loadingRole, setLoadingRole] = useState(null)

  const handleMockLogin = async (role) => {
    setLoadingRole(role)
    // Simular delay de rede
    await new Promise((r) => setTimeout(r, 800))
    login(role)
    navigate(role === 'aluno' ? '/aluno/dashboard' : '/coordenador/dashboard', { replace: true })
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="h-12 w-12 rounded-md bg-primary flex items-center justify-center mb-4 shadow-md">
            <GraduationCap className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-h2 font-bold text-text-primary">AACC Platform</h1>
          <p className="text-label text-text-secondary mt-1">
            Selecione o perfil de teste para continuar
          </p>
        </div>

        {/* Card Mock Login */}
        <div className="surface rounded-sm p-6 shadow-md space-y-4">
          <div className="bg-warning-light border border-warning-muted text-yellow-800 p-3 rounded-xs text-helper mb-4">
            <strong>Modo de Desenvolvimento:</strong> Autenticação via Mock ativa. O JWT real será integrado posteriormente.
          </div>

          <Button 
            fullWidth 
            size="lg" 
            variant="primary" 
            leftIcon={<Users className="h-5 w-5" />}
            loading={loadingRole === 'aluno'}
            onClick={() => handleMockLogin('aluno')}
            disabled={loadingRole !== null}
          >
            Entrar como Aluno
          </Button>

          <Button 
            fullWidth 
            size="lg" 
            variant="secondary" 
            leftIcon={<ShieldAlert className="h-5 w-5 text-text-secondary" />}
            loading={loadingRole === 'coordenador'}
            onClick={() => handleMockLogin('coordenador')}
            disabled={loadingRole !== null}
          >
            Entrar como Coordenador
          </Button>
        </div>
      </div>
    </div>
  )
}
