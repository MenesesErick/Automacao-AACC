/**
 * PerfilConfiguracoes.jsx — UC Perfil e Configurações da Conta
 *
 * Página institucional compartilhada para Aluno, Coordenador e Administrador.
 * - Exibe dados sincronizados da base da universidade (somente leitura / LGPD).
 * - Nome e senha não são editáveis: vêm da view institucional da universidade.
 * - Utiliza Design System Unitins/DSGOV (.surface, unitins-hero-pattern, rounded-xs).
 */

import { useState, useEffect } from 'react'
import { Mail, ShieldCheck, GraduationCap, BookOpen, Award, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/AppLayout'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { useAuth } from '@/contexts/AuthContext'
import { authService } from '@/services/api/endpoints'

function mascararCPF(cpf) {
  if (!cpf) return '—'
  const digits = String(cpf).replace(/\D/g, '')
  if (digits.length === 11) {
    return `${digits.slice(0, 3)}.***.***-${digits.slice(9)}`
  }
  return cpf
}

function extrairIniciais(nome) {
  if (!nome) return 'U'
  return nome
    .trim()
    .split(/\s+/)
    .map(p => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function PerfilConfiguracoes() {
  const { user } = useAuth()
  const [perfil, setPerfil] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function carregarPerfil() {
      try {
        setLoading(true)
        const { data } = await authService.me()
        setPerfil(data)
      } catch (err) {
        toast.error('Erro ao carregar dados do perfil', {
          description: err.response?.data?.detail || err.friendlyMessage || 'Falha na comunicação com o servidor.',
        })
      } finally {
        setLoading(false)
      }
    }
    carregarPerfil()
  }, [])

  const role = perfil?.role || user?.role || 'aluno'
  const LayoutComponent = role === 'admin' ? AdminLayout : AppLayout

  const rotuloPapel = {
    admin: 'ADMINISTRADOR SISTÊMICO',
    coordenador: 'COORDENAÇÃO DE CURSO',
    aluno: 'DISCENTE',
  }[role] || 'USUÁRIO'

  return (
    <LayoutComponent
      title="Meu Perfil e Configurações"
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Conta Institucional</p>
          <h1 className="text-h3 font-bold text-text-primary">Meu Perfil e Configurações</h1>
        </div>
      }
    >
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 text-text-secondary">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
          <p className="text-sm font-medium">Carregando dados da conta...</p>
        </div>
      ) : (
        <div className="max-w-4xl space-y-6">

          {/* ── Banner Superior Institucional ────────────────────────────────── */}
          <div className="unitins-hero-pattern rounded-xs p-6 sm:p-8 text-white border-b-4 border-gold shadow-xs">
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5">
              <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-full bg-[#06182C] border-2 border-gold text-gold font-extrabold text-xl sm:text-2xl flex items-center justify-center shrink-0 shadow-sm">
                {extrairIniciais(perfil?.first_name || user?.nome)}
              </div>
              <div className="flex-1 text-center sm:text-left min-w-0">
                <div className="mb-2">
                  <span className="border border-gold/40 bg-[#0A2540]/80 text-gold text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-xs inline-block">
                    {rotuloPapel}
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white truncate">
                  {perfil?.first_name || user?.nome || 'Usuário'}
                </h2>
                <p className="text-xs sm:text-sm text-white/80 mt-1 flex items-center justify-center sm:justify-start gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-gold shrink-0" />
                  <span>{perfil?.email || user?.email}</span>
                </p>
              </div>
            </div>
          </div>

          {/* ── Card 1: Vínculo Institucional (Somente Leitura - RM) ─────────── */}
          <div className="surface rounded-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-[#F8FAFC]">
              <h2 className="text-xs font-extrabold uppercase tracking-wider text-primary flex items-center">
                <span className="w-1 h-4 bg-gold mr-2 inline-block" />
                Vínculo Institucional (Somente Leitura)
              </h2>
              <p className="text-helper text-text-secondary mt-0.5">
                Dados sincronizados passivamente com o Sistema Acadêmico da Unitins.
              </p>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* E-mail Institucional */}
              <div className="p-3.5 rounded-xs border border-border bg-bg/60">
                <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-primary" /> E-mail Institucional
                </p>
                <p className="text-sm font-semibold text-text-primary break-all">{perfil?.email || '—'}</p>
              </div>

              {/* CPF Mascarado */}
              <div className="p-3.5 rounded-xs border border-border bg-bg/60">
                <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-primary" /> CPF (LGPD)
                </p>
                <p className="text-sm font-semibold text-text-primary font-mono">{mascararCPF(perfil?.cpf)}</p>
              </div>

              {/* Campos específicos por perfil */}
              {role === 'aluno' && (
                <>
                  <div className="p-3.5 rounded-xs border border-border bg-bg/60">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                      <GraduationCap className="h-3.5 w-3.5 text-primary" /> Matrícula Acadêmica
                    </p>
                    <p className="text-sm font-semibold text-text-primary font-mono">{perfil?.matricula || '—'}</p>
                  </div>

                  <div className="p-3.5 rounded-xs border border-border bg-bg/60">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                      <BookOpen className="h-3.5 w-3.5 text-primary" /> Curso Vinculado
                    </p>
                    <p className="text-sm font-semibold text-text-primary">{perfil?.curso_nome || '—'}</p>
                  </div>

                  <div className="p-3.5 rounded-xs border border-border bg-bg/60 md:col-span-2">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                      <Award className="h-3.5 w-3.5 text-primary" /> Matriz Curricular (Exigência AACC)
                    </p>
                    <p className="text-sm font-semibold text-text-primary">
                      {perfil?.horas_totais_exigidas ? `${perfil.horas_totais_exigidas}h exigidas no projeto pedagógico` : '—'}
                    </p>
                  </div>
                </>
              )}

              {role === 'coordenador' && (
                <div className="p-3.5 rounded-xs border border-border bg-bg/60 md:col-span-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5 text-primary" /> Curso sob sua Coordenação
                  </p>
                  <p className="text-sm font-semibold text-text-primary">{perfil?.curso_nome || '—'}</p>
                </div>
              )}

              {role === 'admin' && (
                <div className="p-3.5 rounded-xs border border-border bg-bg/60 md:col-span-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary mb-1 flex items-center gap-1.5">
                    <Award className="h-3.5 w-3.5 text-primary" /> Atribuição Funcional
                  </p>
                  <p className="text-sm font-semibold text-text-primary">{perfil?.cargo || 'Administrador Sistêmico'}</p>
                </div>
              )}
            </div>

            <div className="px-6 py-3 border-t border-border bg-[#F8FAFC]/50 flex items-center gap-2 text-helper text-text-secondary">
              <ShieldCheck className="h-4 w-4 text-primary shrink-0" />
              <span>
                Dados sincronizados de forma passiva com o Sistema de Registros Acadêmicos (RM/Unitins) e protegidos conforme diretrizes da LGPD.
              </span>
            </div>
          </div>

        </div>
      )}
    </LayoutComponent>
  )
}
