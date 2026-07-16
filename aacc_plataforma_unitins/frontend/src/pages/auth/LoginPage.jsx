import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GraduationCap, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [erro,     setErro]     = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')

    // Validação de domínio no cliente (espelho da regra do backend)
    if (!email.toLowerCase().endsWith('@unitins.br')) {
      setErro('Apenas e-mails institucionais (@unitins.br) são permitidos.')
      return
    }

    setLoading(true)
    try {
      const perfil = await login(email, password)
      navigate(`/${perfil.role}/dashboard`, { replace: true })
    } catch (err) {
      // Mensagem amigável do interceptor do Axios
      setErro(
        err?.friendlyMessage ??
        err?.response?.data?.detail ??
        'Credenciais inválidas. Verifique o e-mail e a senha.'
      )
    } finally {
      setLoading(false)
    }
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
            Unitins — Acesso restrito a e-mails institucionais
          </p>
        </div>

        {/* Card de login */}
        <div className="surface rounded-sm p-6 shadow-md">
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>

            {/* E-mail */}
            <div>
              <label htmlFor="email" className="text-label font-medium text-text-primary mb-1.5 block">
                E-mail institucional
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary pointer-events-none" />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="seu.nome@unitins.br"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 h-10 rounded-xs border border-border bg-bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
                  required
                />
              </div>
            </div>

            {/* Senha */}
            <div>
              <label htmlFor="password" className="text-label font-medium text-text-primary mb-1.5 block">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary pointer-events-none" />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 h-10 rounded-xs border border-border bg-bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
                  required
                />
              </div>
            </div>

            {/* Mensagem de erro */}
            {erro && (
              <div className="flex items-start gap-2.5 text-danger bg-danger-light border border-danger-muted rounded-xs p-3">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <p className="text-helper">{erro}</p>
              </div>
            )}

            {/* Botão de submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full h-10 rounded-xs bg-primary text-text-inverse font-medium text-label flex items-center justify-center gap-2 hover:bg-primary-hover transition-colors disabled:opacity-60 disabled:cursor-not-allowed shadow-xs"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  A autenticar...
                </>
              ) : 'Entrar'}
            </button>
          </form>
        </div>

        <p className="text-center text-helper text-text-disabled mt-6">
          AACC Platform © {new Date().getFullYear()} — Unitins
        </p>
      </div>
    </div>
  )
}
