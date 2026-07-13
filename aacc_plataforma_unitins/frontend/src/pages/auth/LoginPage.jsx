import { useState } from 'react'
import { GraduationCap, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'

export default function LoginPage() {
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading]   = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    // TODO: integrar authService.login()
    await new Promise((r) => setTimeout(r, 1200))
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      {/* Painel central */}
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-md bg-primary flex items-center justify-center mb-4 shadow-md">
            <GraduationCap className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-h2 font-bold text-text-primary">AACC Platform</h1>
          <p className="text-label text-text-secondary mt-1">Acesse sua conta UNITINS</p>
        </div>

        {/* Card */}
        <div className="surface rounded-sm p-6 shadow-md">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="E-mail institucional"
              type="email"
              placeholder="seu@unitins.br"
              fullWidth
              required
              autoComplete="email"
            />

            <Input
              label="Senha"
              type={showPass ? 'text' : 'password'}
              placeholder="••••••••"
              fullWidth
              required
              autoComplete="current-password"
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="text-text-secondary hover:text-text-primary transition-colors"
                  tabIndex={-1}
                >
                  {showPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              }
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded accent-primary" />
                <span className="text-label text-text-secondary">Lembrar-me</span>
              </label>
              <a href="#" className="text-label text-primary hover:text-primary-hover font-medium transition-colors">
                Esqueci a senha
              </a>
            </div>

            <Button type="submit" fullWidth loading={loading} size="lg">
              Entrar
            </Button>
          </form>
        </div>

        <p className="text-center text-helper text-text-secondary mt-6">
          AACC Platform · UNITINS — {new Date().getFullYear()}
        </p>
      </div>
    </div>
  )
}
