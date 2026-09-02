import { useState, useEffect, useCallback } from 'react'
import {
  CheckCircle, XCircle, Clock, Eye, AlertCircle,
  FileText, Plus, ChevronLeft
} from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { certificadosService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

// ── Configuração semântica de status ─────────────────────────────────────────
const STATUS_CONFIG = {
  aprovado: {
    label:   'Aprovado',
    icon:    CheckCircle,
    dot:     'bg-success',
    ring:    'ring-success-muted',
    card:    'border-success-muted bg-success-light/40',
    text:    'text-success',
    badge:   'bg-success-light text-success',
  },
  rejeitado: {
    label:   'Rejeitado',
    icon:    XCircle,
    dot:     'bg-danger',
    ring:    'ring-danger-muted',
    card:    'border-danger-muted bg-danger-light/40',
    text:    'text-danger',
    badge:   'bg-danger-light text-danger',
  },
  revisao_manual: {
    label:   'Revisão Manual',
    icon:    Eye,
    dot:     'bg-warning',
    ring:    'ring-warning-muted',
    card:    'border-warning-muted bg-warning-light/40',
    text:    'text-yellow-700',
    badge:   'bg-warning-light text-yellow-700',
  },
  pendente_ocr: {
    label:   'Aguardando OCR',
    icon:    Clock,
    dot:     'bg-primary',
    ring:    'ring-primary-muted',
    card:    'border-border bg-bg',
    text:    'text-primary',
    badge:   'bg-primary-light text-primary',
  },
  requerimento_gerado: {
    label:   'Requerimento Gerado',
    icon:    CheckCircle,
    dot:     'bg-secondary',
    ring:    'ring-primary-muted',
    card:    'border-primary-muted bg-primary-light/30',
    text:    'text-secondary',
    badge:   'bg-primary-light text-secondary',
  },
}

const DEFAULT_CONFIG = {
  label:   'Pendente',
  icon:    Clock,
  dot:     'bg-border-strong',
  ring:    'ring-border',
  card:    'border-border bg-bg',
  text:    'text-text-secondary',
  badge:   'bg-bg text-text-secondary',
}

// ── Formatação de data ────────────────────────────────────────────────────────
function formatarData(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('pt-BR', {
    day:   '2-digit',
    month: 'long',
    year:  'numeric',
  })
}

function formatarDataHora(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', {
    day:    '2-digit',
    month:  '2-digit',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
  })
}

// ── Card da Timeline ──────────────────────────────────────────────────────────
function TimelineItem({ cert, isLast, onClick }) {
  const cfg = STATUS_CONFIG[cert.status] ?? DEFAULT_CONFIG
  const Icon = cfg.icon

  return (
    <li className="relative flex gap-4 group">
      {/* Linha vertical (omitida no último item) */}
      {!isLast && (
        <span
          className="absolute left-4 top-9 w-0.5 bg-border"
          style={{ bottom: '-16px' }}
          aria-hidden="true"
        />
      )}

      {/* Bolinha do nó */}
      <div className="relative z-10 flex items-start pt-1 shrink-0">
        <span
          className={cn(
            'h-8 w-8 rounded-full ring-4 flex items-center justify-center shrink-0',
            cfg.dot,
            cfg.ring,
          )}
        >
          <Icon className="h-4 w-4 text-white" strokeWidth={2.5} />
        </span>
      </div>

      {/* Card de conteúdo */}
      <button
        onClick={() => onClick(cert)}
        className={cn(
          'flex-1 mb-4 text-left rounded-sm border p-4 transition-shadow duration-normal',
          'hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          cfg.card,
        )}
      >
        {/* Linha superior: categoria + badge + acao */}
        <div className="flex items-start justify-between gap-3">
          <p className="text-label font-semibold text-text-primary leading-snug line-clamp-2">
            {cert.categoria_nome ?? 'Categoria não identificada'}
          </p>
          <div className="flex items-center gap-2 shrink-0">
            <span className={cn('text-helper font-semibold px-2 py-0.5 rounded-full', cfg.badge)}>
              {cfg.label}
            </span>
            <span className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 text-helper text-text-secondary">
              <Eye className="h-3.5 w-3.5" /> Visualizar
            </span>
          </div>
        </div>

        {/* Linha de horas */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
          <span className="text-helper text-text-secondary">
            Sugeridas / Declaradas: <strong className="text-text-primary">{cert.horas_sugeridas_ia ?? cert.horas_declaradas ?? 0}h</strong>
          </span>
          {cert.horas_computadas_final != null && (
            <span className="text-helper text-text-secondary">
              Computadas: <strong className={cfg.text}>{cert.horas_computadas_final}h</strong>
            </span>
          )}
        </div>

        {/* Motivo do status (especialmente útil para rejeições/revisões) */}
        {cert.motivo_status && cert.status !== 'rejeitado' && (
          <div className="mt-2 pt-2 border-t border-black/5">
            <p className="text-helper text-text-secondary italic line-clamp-2">
              <span className="font-semibold not-italic text-text-primary">Observação: </span>
              {cert.motivo_status}
            </p>
          </div>
        )}

        {/* ── Bloco de Indeferimento Oficial (RN03) ──────────────────────── */}
        {cert.status === 'rejeitado' && (
          <div className="mt-3 rounded-xs border border-danger-muted bg-danger-light/50 overflow-hidden">
            {/* Cabeçalho */}
            <div className="flex items-center gap-2 px-3 py-2 bg-danger/10 border-b border-danger-muted">
              <XCircle className="h-3.5 w-3.5 text-danger shrink-0" />
              <p className="text-helper font-bold text-danger uppercase tracking-wide">
                Documento Indeferido pela Coordenação
              </p>
            </div>
            {/* Corpo */}
            <div className="px-3 py-2.5">
              <p className="text-helper font-bold text-danger/80 mb-1">
                Justificativa da Coordenação:
              </p>
              <p className="text-helper text-text-primary leading-relaxed">
                {cert.justificativa_indeferimento
                  || cert.motivo_status
                  || 'Sem justificativa registrada. Entre em contacto com a coordenação.'}
              </p>
            </div>
          </div>
        )}

        {/* Rodapé: datas */}
        <div className="flex flex-wrap gap-x-4 mt-2.5">
          {cert.data_envio && (
            <p className="text-helper text-text-disabled">
              Enviado em {formatarDataHora(cert.data_envio)}
            </p>
          )}
          {cert.atualizado_em && cert.atualizado_em !== cert.data_envio && (
            <p className="text-helper text-text-disabled">
              Atualizado em {formatarDataHora(cert.atualizado_em)}
            </p>
          )}
        </div>
      </button>
    </li>
  )
}

// ── Skeleton Loading ──────────────────────────────────────────────────────────
function TimelineSkeleton() {
  return (
    <ul className="pl-0 space-y-0">
      {[...Array(4)].map((_, i) => (
        <li key={i} className="relative flex gap-4">
          <div className="relative z-10 flex items-start pt-1 shrink-0">
            <span className="h-8 w-8 rounded-full bg-border animate-pulse" />
          </div>
          <div className="flex-1 mb-4 rounded-sm border border-border p-4 animate-pulse">
            <div className="h-4 bg-border rounded w-2/3 mb-3" />
            <div className="h-3 bg-border rounded w-1/3 mb-2" />
            <div className="h-3 bg-border rounded w-1/2" />
          </div>
        </li>
      ))}
    </ul>
  )
}

// ── Componente Principal ──────────────────────────────────────────────────────
export default function HistoricoAluno() {
  const navigate = useNavigate()
  const [certificados, setCertificados] = useState([])
  const [loading,      setLoading]      = useState(true)
  const [erro,         setErro]         = useState(null)

  const fetchHistorico = useCallback(async () => {
    try {
      setLoading(true)
      const { data } = await certificadosService.listar()
      const lista = Array.isArray(data) ? data : (data.results ?? [])
      // Ordena do mais recente para o mais antigo
      lista.sort((a, b) => {
        const da = new Date(a.atualizado_em ?? a.data_envio ?? 0)
        const db = new Date(b.atualizado_em ?? b.data_envio ?? 0)
        return db - da
      })
      setCertificados(lista)
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar histórico de certificados.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchHistorico() }, [fetchHistorico])

  // Agrupa por mês/ano para criar secções na timeline
  const grupos = certificados.reduce((acc, cert) => {
    const dt  = cert.atualizado_em ?? cert.data_envio
    const key = dt
      ? new Date(dt).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
      : 'Data desconhecida'
    if (!acc[key]) acc[key] = []
    acc[key].push(cert)
    return acc
  }, {})

  return (
    <AppLayout
      breadcrumb={
        <div className="min-w-0">
          <p className="text-helper text-text-secondary">Portal do Aluno</p>
          <h1 className="text-h4 font-bold text-text-primary truncate">Meu Histórico</h1>
        </div>
      }
    >
      {/* Cabeçalho da página */}
      <div className="flex items-center justify-between mb-6 gap-4">
        <div>
          <h2 className="text-h3 font-bold text-text-primary">Jornada dos Certificados</h2>
          <p className="text-label text-text-secondary mt-1">
            {loading
              ? 'Carregando...'
              : `${certificados.length} registro(s) no histórico — do mais recente ao mais antigo.`}
          </p>
        </div>
        <Link
          to="/aluno/enviar"
          className="flex items-center gap-2 px-4 h-9 rounded-xs bg-primary text-white text-label font-medium hover:bg-primary-hover transition-colors shrink-0 shadow-xs"
        >
          <Plus className="h-4 w-4" />
          Enviar Certificado
        </Link>
      </div>

      {/* Erro */}
      {erro && (
        <div className="surface rounded-sm p-6 flex items-center gap-3 text-danger mb-4">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-label">{erro}</p>
        </div>
      )}

      {/* Skeleton */}
      {loading && <TimelineSkeleton />}

      {/* Estado vazio */}
      {!loading && !erro && certificados.length === 0 && (
        <div className="surface rounded-sm p-12 flex flex-col items-center gap-4 text-center">
          <div className="h-12 w-12 rounded-xl bg-primary-light flex items-center justify-center">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <p className="text-label font-semibold text-text-primary">Nenhum certificado ainda</p>
            <p className="text-helper text-text-secondary mt-1">
              Envie seu primeiro certificado para começar a jornada AACC.
            </p>
          </div>
          <Link
            to="/aluno/enviar"
            className="flex items-center gap-2 px-4 h-9 rounded-xs bg-primary text-white text-label font-medium hover:bg-primary-hover transition-colors"
          >
            <Plus className="h-4 w-4" />
            Enviar agora
          </Link>
        </div>
      )}

      {/* Timeline agrupada por mês */}
      {!loading && !erro && certificados.length > 0 && (
        <div className="space-y-6">
          {Object.entries(grupos).map(([mesAno, items]) => (
            <section key={mesAno}>
              {/* Separador de período */}
              <div className="flex items-center gap-3 mb-3">
                <span className="text-helper font-bold text-text-disabled uppercase tracking-widest capitalize">
                  {mesAno}
                </span>
                <span className="flex-1 h-px bg-border" />
                <span className="text-helper text-text-disabled">{items.length} item(s)</span>
              </div>

              {/* Lista de nós */}
              <ul className="ml-0 space-y-0">
                {items.map((cert, idx) => (
                  <TimelineItem
                    key={cert.id}
                    cert={cert}
                    isLast={idx === items.length - 1}
                    onClick={() => navigate(`/aluno/certificados/${cert.id}`)}
                  />
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </AppLayout>
  )
}
