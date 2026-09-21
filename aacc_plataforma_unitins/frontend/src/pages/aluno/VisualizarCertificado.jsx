/**
 * VisualizarCertificado.jsx — Modo Foco do Aluno
 *
 * Layout split-screen read-only:
 *   ├─ Esquerda (flex-1) : iframe do PDF em altura máxima
 *   └─ Direita  (w-96)   : status, metadados e justificativa (sem botões de avaliação)
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, CheckCircle2, Loader2,
  AlertTriangle, Hourglass, Layers, Hash,
  Calendar, TrendingDown, Info, BadgeCheck, MessageSquareX, Clock
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { certificadosService } from '@/services/api/endpoints'

// ─── helpers ─────────────────────────────────────────────────────────────────

function MetaRow({ icon: Icon, label, value, valueClass = '' }) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-border last:border-0">
      <div className="h-7 w-7 rounded-xs bg-bg flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="h-3.5 w-3.5 text-text-secondary" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-helper text-text-secondary leading-none">{label}</p>
        <p className={cn('text-label font-semibold text-text-primary mt-0.5 break-words', valueClass)}>
          {value ?? '—'}
        </p>
      </div>
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <p className="text-helper font-bold text-text-disabled uppercase tracking-widest mb-3">
      {children}
    </p>
  )
}

const STATUS_CFG = {
  revisao_manual: { label: 'Em Análise', cls: 'bg-warning-light text-yellow-700 border-warning-muted' },
  pendente_ocr:   { label: 'Em Análise', cls: 'bg-warning-light text-yellow-700 border-warning-muted' },
  aprovado:       { label: 'Aprovado',   cls: 'bg-success-light text-success border-success-muted' },
  rejeitado:      { label: 'Rejeitado',  cls: 'bg-danger-light text-danger border-danger-muted' },
}

// ─── Banner de Status ─────────────────────────────────────────────────────

function BannerStatus({ cert }) {
  const isAprovado = cert.status === 'aprovado'
  const isRejeitado = cert.status === 'rejeitado'
  const isPendente = ['pendente_ocr', 'revisao_manual'].includes(cert.status)

  if (isAprovado) {
    return (
      <div className="rounded-sm border-2 border-success bg-success-light p-5 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-success/20 flex items-center justify-center shrink-0">
            <BadgeCheck className="h-5 w-5 text-success" />
          </div>
          <div>
            <p className="text-label font-bold text-success">Documento Aprovado</p>
            <p className="text-helper text-success/70">A coordenação deferiu as suas horas.</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="bg-white/60 rounded-xs p-2.5 text-center">
            <p className="text-helper text-text-secondary">Horas Deferidas</p>
            <p className="text-h4 font-bold text-success">
              {cert.horas_computadas_final ?? '—'}h
            </p>
          </div>
          <div className="bg-white/60 rounded-xs p-2.5 text-center">
            <p className="text-helper text-text-secondary">Horas Cortadas</p>
            <p className="text-h4 font-bold text-text-secondary">
              {Number(cert.horas_descartadas) > 0 ? `-${cert.horas_descartadas}h` : '0h'}
            </p>
          </div>
        </div>

        {cert.motivo_status && (
          <div className="flex items-start gap-2 pt-1 border-t border-success/20">
            <Info className="h-3.5 w-3.5 text-success shrink-0 mt-0.5" />
            <p className="text-helper text-success/80 italic">{cert.motivo_status}</p>
          </div>
        )}
      </div>
    )
  }

  if (isRejeitado) {
    return (
      <div className="rounded-sm border-2 border-danger bg-danger-light p-5 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-danger/20 flex items-center justify-center shrink-0">
            <MessageSquareX className="h-5 w-5 text-danger" />
          </div>
          <div>
            <p className="text-label font-bold text-danger">Documento Indeferido</p>
            <p className="text-helper text-danger/70">Este certificado não pôde ser aproveitado.</p>
          </div>
        </div>

        <div className="bg-white/70 rounded-xs p-3 border border-danger/20">
          <p className="text-helper font-bold text-danger mb-1.5">Justificativa da Coordenação:</p>
          <p className="text-label text-text-primary leading-relaxed">
            {cert.justificativa_indeferimento || cert.motivo_status || 'Sem justificativa registrada.'}
          </p>
        </div>
      </div>
    )
  }

  // Pendente / Revisão
  return (
    <div className="rounded-sm border-2 border-primary/30 bg-primary/5 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
          <Clock className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-label font-bold text-primary">Em Análise</p>
          <p className="text-helper text-text-secondary">
            Este documento está aguardando auditoria da coordenação.
          </p>
        </div>
      </div>
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────

export default function VisualizarCertificado() {
  const { id }     = useParams()
  const navigate   = useNavigate()

  const [cert,          setCert]         = useState(null)
  const [loading,       setLoading]      = useState(true)
  const [erro,          setErro]         = useState(null)

  useEffect(() => {
    setLoading(true)
    certificadosService.obter(id)
      .then(({ data }) => {
        setCert(data)
      })
      .catch((e) => setErro(e.friendlyMessage ?? 'Erro ao carregar certificado.'))
      .finally(() => setLoading(false))
  }, [id])

  const getPdfUrl = (path) => {
    if (!path) return null
    if (path.startsWith('http')) return path
    const clean = path.startsWith('/media') ? path : `/media/${path}`
    const origin = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api\/?$/, '')
    return `${origin}${clean}`
  }

  // ── Loading / erro ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (erro || !cert) {
    return (
      <div className="min-h-screen bg-bg flex flex-col items-center justify-center gap-4 text-danger">
        <AlertTriangle className="h-10 w-10" />
        <p className="text-label font-semibold">{erro ?? 'Certificado não encontrado.'}</p>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-4 h-9 rounded-xs bg-primary text-white text-label font-medium"
        >
          <ArrowLeft className="h-4 w-4" /> Voltar
        </button>
      </div>
    )
  }

  const pdfUrl      = getPdfUrl(cert.arquivo_pdf)
  const statusCfg   = STATUS_CFG[cert.status] ?? STATUS_CFG.pendente_ocr
  const dataEnvio   = cert.data_envio
    ? new Date(cert.data_envio).toLocaleString('pt-BR', {
        day: '2-digit', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : '—'

  return (
    <div className="min-h-screen bg-bg flex flex-col">

      {/* ── Barra de topo ─────────────────────────────────────────────────── */}
      <header className="h-14 bg-bg-surface border-b border-border flex items-center gap-4 px-4 shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-label text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </button>

        <span className="text-border">|</span>

        <div className="flex items-center gap-2 min-w-0">
          <span className="text-label font-bold text-text-primary truncate">
            Certificado #{cert.id}
          </span>
          <span className={cn(
            'text-helper font-semibold px-2 py-0.5 rounded-full border shrink-0',
            statusCfg.cls,
          )}>
            {statusCfg.label}
          </span>
        </div>
      </header>

      {/* ── Split-screen ──────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* ╔══════════════════════════════════════╗
            ║  ESQUERDA — Visualizador de PDF      ║
            ╚══════════════════════════════════════╝ */}
        <div className="flex-1 flex flex-col bg-bg p-4 min-w-0 border-r border-border overflow-hidden">
          <p className="text-helper font-bold text-text-disabled uppercase tracking-widest mb-3 shrink-0">
            Documento Certificado
          </p>

          {pdfUrl ? (
            <iframe
              src={pdfUrl}
              title={`PDF Certificado #${cert.id}`}
              className="flex-1 rounded-sm border border-border bg-white w-full min-h-0"
              style={{ minHeight: 0 }}
            />
          ) : (
            <div className="flex-1 rounded-sm border border-border bg-bg-surface flex flex-col items-center justify-center gap-3 text-center p-8">
              <AlertTriangle className="h-10 w-10 text-text-disabled" />
              <p className="text-label font-medium text-text-secondary">PDF não disponível</p>
            </div>
          )}
        </div>

        {/* ╔══════════════════════════════════════╗
            ║  DIREITA — Painel de Resumo          ║
            ╚══════════════════════════════════════╝ */}
        <aside className="w-96 shrink-0 flex flex-col overflow-y-auto bg-bg-surface">
          <div className="p-5 space-y-5">

            {/* 1. Status Geral (Banner) */}
            <div>
              <SectionTitle>Status da Avaliação</SectionTitle>
              <BannerStatus cert={cert} />
            </div>

            {/* 2. Informações do Documento */}
            <div>
              <SectionTitle>Detalhes do Documento</SectionTitle>
              <div className="bg-bg rounded-sm border border-border">
                <MetaRow icon={Layers}   label="Categoria"     value={cert.categoria_nome} />
                <MetaRow icon={Calendar} label="Data de Envio" value={dataEnvio} />
                <MetaRow
                  icon={Hourglass}
                  label="Horas Declaradas"
                  value={cert.horas_declaradas != null ? `${cert.horas_declaradas}h` : '—'}
                  valueClass="text-primary"
                />
                
                {cert.status === 'aprovado' && cert.horas_computadas_final != null && (
                  <MetaRow
                    icon={CheckCircle2}
                    label="Horas Computadas"
                    value={`${cert.horas_computadas_final}h`}
                    valueClass="text-success font-bold"
                  />
                )}
                {cert.status === 'aprovado' && Number(cert.horas_descartadas) > 0 && (
                  <MetaRow
                    icon={TrendingDown}
                    label="Horas Cortadas (SEBR)"
                    value={`-${cert.horas_descartadas}h`}
                    valueClass="text-danger"
                  />
                )}
                <MetaRow icon={Hash} label="ID Interno" value={`#${cert.id}`} />
              </div>
            </div>

          </div>
        </aside>
      </div>
    </div>
  )
}
