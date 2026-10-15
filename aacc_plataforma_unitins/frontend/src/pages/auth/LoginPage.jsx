import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mail, Lock, AlertCircle, Loader2 } from 'lucide-react'
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

  const inputCls =
    'w-full pl-9 pr-3 h-11 rounded-xs border border-border bg-bg-surface text-sm text-text-primary ' +
    'placeholder:text-text-disabled focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary'
  const labelCls = 'text-xs font-bold uppercase tracking-wider text-text-primary mb-1.5 block'

  return (
    <div className="min-h-screen bg-bg flex flex-col">

      {/* ── Cabeçalho institucional ─────────────────────────────────────── */}
      <div className="unitins-gold-bar w-full" />
      <header className="bg-white border-b border-border px-6 py-3 flex items-center justify-between">
        <div className="flex items-center">
          <span className="font-extrabold tracking-widest text-primary text-sm uppercase">Unitins</span>
          <span className="h-4 w-px bg-border-strong mx-3" />
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
            Sistema de Gestão AACC
          </span>
        </div>
        <span className="text-[11px] font-bold tracking-wider text-text-secondary uppercase hidden sm:block">
          Tocantins | Governo do Estado
        </span>
      </header>

      {/* ── Split-screen ────────────────────────────────────────────────── */}
      <main className="flex-1 flex">

        {/* Painel institucional (desktop) */}
        <section className="unitins-hero-pattern hidden lg:flex flex-1 flex-col justify-center px-16 xl:px-24 py-12 text-white">
          <div className="max-w-xl">
            <span className="border border-gold/40 bg-[#0A2540]/60 text-gold text-[11px] font-bold uppercase tracking-widest px-3 py-1 rounded-xs inline-block">
              Resolução CONSUNI Nº 057/2025
            </span>

            <h1 className="text-2xl xl:text-3xl font-extrabold tracking-tight text-white mt-4">
              Plataforma Integrada de Contabilização e Auditoria de AACC
            </h1>

            <p className="text-sm text-white/80 leading-relaxed mt-4">
              Modernização do fluxo das Atividades Acadêmico-Científico-Culturais da Unitins:
              do envio do certificado pelo aluno à homologação final pela coordenação,
              com rastreabilidade e total aderência à resolução vigente.
            </p>

            <ul className="mt-6 space-y-3 text-sm text-white/90">
              <li className="flex gap-3">
                <span className="text-gold font-bold">&gt;</span>
                Extração assistida de metadados via Visão Computacional (OCR)
              </li>
              <li className="flex gap-3">
                <span className="text-gold font-bold">&gt;</span>
                Cômputo determinístico de limites por Eixo e Categoria
              </li>
              <li className="flex gap-3">
                <span className="text-gold font-bold">&gt;</span>
                Emissão homologada do Requerimento Oficial (Anexo I)
              </li>
            </ul>
          </div>
        </section>

        {/* Área do card de autenticação */}
        <section className="flex-1 flex items-center justify-center p-6 bg-bg">
          <div className="surface rounded-xs border-t-4 border-primary p-8 w-full max-w-md">

            <div className="mb-6">
              <h2 className="text-lg font-extrabold uppercase tracking-wider text-primary">
                Acesso Autenticado
              </h2>
              <p className="text-helper text-text-secondary mt-1">
                Acesse com suas credenciais institucionais (@unitins.br).
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5" noValidate>

              {/* E-mail */}
              <div>
                <label htmlFor="email" className={labelCls}>E-mail institucional</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary pointer-events-none" />
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="seu.nome@unitins.br"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={inputCls}
                    required
                  />
                </div>
              </div>

              {/* Senha */}
              <div>
                <label htmlFor="password" className={labelCls}>Senha</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary pointer-events-none" />
                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={inputCls}
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
                className="w-full h-11 rounded-xs bg-primary hover:bg-primary-hover text-white font-bold uppercase tracking-wider text-xs flex items-center justify-center gap-2 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
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
        </section>
      </main>

      {/* ── Rodapé institucional ────────────────────────────────────────── */}
      <footer className="text-[11px] text-text-secondary text-center py-3 border-t border-border bg-white">
        Universidade Estadual do Tocantins (Unitins) — Câmpus Palmas | Curso de Sistemas de Informação
      </footer>
    </div>
  )
}
