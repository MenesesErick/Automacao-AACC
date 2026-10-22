/**
 * AvaliarCertificado.jsx — Modo Foco do Coordenador
 *
 * Layout split-screen:
 *   ├─ Esquerda (flex-1) : iframe do PDF em altura máxima
 *   └─ Direita  (w-96)   : identidade do aluno + metadados OCR + decisão SEBR
 *
 * Novas features (Ideias A, B, C):
 *   A) Rastro de Auditoria Textual  — mensagens humanas sobre cortes SEBR
 *   B) Termômetro Visual de Saldo   — barra de progresso por categoria
 *   C) Modal "Ver Regra"            — tooltip oficial da Resolução 057
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, CheckCircle2, XCircle, Loader2,
  AlertTriangle, Hourglass, Eye, Layers, Hash,
  Calendar, TrendingDown, ShieldCheck, Info, Scissors,
  UserCircle, GraduationCap, BadgeCheck, MessageSquareX,
  BookOpen, X as XIcon, AlertCircle, FileText, CalendarRange, Clock, ChevronDown,
} from 'lucide-react'
import { toast } from 'sonner'
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
  revisao_manual: { label: 'Revisão Manual', cls: 'bg-warning-light text-yellow-700 border-warning-muted' },
  pendente_ocr:   { label: 'Pendente OCR',   cls: 'bg-bg text-text-secondary border-border' },
  aprovado:       { label: 'Aprovado',        cls: 'bg-success-light text-success border-success-muted' },
  rejeitado:      { label: 'Rejeitado',       cls: 'bg-danger-light text-danger border-danger-muted' },
}

// ─── Ideia C: Modal "Ver Regra" ───────────────────────────────────────────────

function ModalRegra({ regra, onClose }) {
  if (!regra) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Card */}
      <div
        className="relative z-10 w-full max-w-lg bg-bg-surface rounded-sm border border-border shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 p-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xs bg-primary/10 flex items-center justify-center shrink-0">
              <BookOpen className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-label font-bold text-text-primary">{regra.nome}</p>
              <p className="text-helper text-text-secondary">Eixo: {regra.eixo}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="h-7 w-7 flex items-center justify-center rounded-xs text-text-secondary hover:bg-bg hover:text-text-primary transition-colors"
          >
            <XIcon className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          {/* Texto oficial */}
          <div className="bg-primary-light/60 border border-primary-muted rounded-xs p-3">
            <p className="text-helper font-bold text-primary mb-1.5">Texto Oficial — Resolução CONSUNI Nº 057/2025</p>
            <p className="text-label text-text-primary leading-relaxed">
              {regra.tooltip || 'Descrição não disponível para esta categoria.'}
            </p>
          </div>

          {/* Limites normativos */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-bg rounded-xs border border-border p-3 text-center">
              <p className="text-helper text-text-secondary">Teto por Evento</p>
              <p className="text-card font-bold text-text-primary mt-0.5">
                {regra.teto_por_evento != null ? `${regra.teto_por_evento}h` : '∞'}
              </p>
            </div>
            <div className="bg-bg rounded-xs border border-border p-3 text-center">
              <p className="text-helper text-text-secondary">Teto Total no Curso</p>
              <p className="text-card font-bold text-text-primary mt-0.5">
                {regra.teto_total != null ? `${regra.teto_total}h` : '∞'}
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-border flex justify-end">
          <button
            onClick={onClose}
            className="px-4 h-9 rounded-xs bg-primary text-white text-label font-medium hover:bg-primary-hover transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Ideia B: Termômetro de Saldo da Categoria ───────────────────────────────

function TermometroCategoriaCard({ cert, onVerRegra }) {
  const cat    = cert.categoria_obj
  const saldo  = parseFloat(cert.saldo_atual_categoria ?? 0)
  const teto   = cat?.teto_total

  const pct    = teto ? Math.min(Math.round((saldo / teto) * 100), 100) : null
  const isCheio = pct != null && pct >= 100

  return (
    <div className="bg-bg rounded-sm border border-border p-3 space-y-2.5">
      {/* Linha nome + botão Ver Regra */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Layers className="h-3.5 w-3.5 text-text-secondary shrink-0" />
          <p className="text-label font-semibold text-text-primary truncate">
            {cat?.nome ?? cert.categoria_nome}
          </p>
        </div>
        {cat?.tooltip && (
          <button
            onClick={onVerRegra}
            className="flex items-center gap-1 text-helper text-primary hover:text-primary-hover transition-colors shrink-0"
          >
            <BookOpen className="h-3.5 w-3.5" />
            Ver Regra
          </button>
        )}
      </div>

      {/* Barra de progresso */}
      {teto != null ? (
        <>
          <div className="w-full h-2 bg-bg-surface rounded-full overflow-hidden border border-border">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                pct >= 100 ? 'bg-danger' : pct >= 70 ? 'bg-warning' : 'bg-success',
              )}
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-helper text-text-secondary">
              Saldo atual:{' '}
              <span className={cn('font-semibold', isCheio ? 'text-danger' : 'text-text-primary')}>
                {saldo}h
              </span>
              {' '}de{' '}
              <span className="font-semibold text-text-primary">{teto}h</span>
              {' '}permitidas
            </p>
            <span className={cn(
              'text-helper font-bold',
              pct >= 100 ? 'text-danger' : pct >= 70 ? 'text-warning' : 'text-success',
            )}>
              {pct}%
            </span>
          </div>
          {isCheio && (
            <div className="flex items-center gap-1.5 text-danger">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              <p className="text-helper font-semibold">
                Teto atingido — o SEBR zerará as horas nesta categoria.
              </p>
            </div>
          )}
        </>
      ) : (
        <p className="text-helper text-text-secondary">
          Saldo atual:{' '}
          <span className="font-semibold text-text-primary">{saldo}h</span>
          {' '}— categoria sem teto total definido
        </p>
      )}

      {/* Teto por evento */}
      {cat?.teto_por_evento != null && (
        <div className="flex items-center gap-1.5 border-t border-border pt-2">
          <Scissors className="h-3 w-3 text-text-secondary" />
          <p className="text-helper text-text-secondary">
            Limite por certificado:{' '}
            <span className="font-semibold text-text-primary">{cat.teto_por_evento}h</span>
          </p>
        </div>
      )}
    </div>
  )
}

// ─── Card de Identidade do Aluno ─────────────────────────────────────────────

function CardAluno({ cert }) {
  return (
    <div className="rounded-sm border border-primary/20 bg-primary/5 p-4">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
          <UserCircle className="h-6 w-6 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-label font-bold text-text-primary truncate">
            {cert.aluno_nome ?? 'Aluno não identificado'}
          </p>
          <p className="text-helper text-text-secondary mt-0.5">
            Matrícula: <span className="font-semibold text-text-primary font-mono">{cert.aluno_matricula ?? '—'}</span>
          </p>
        </div>
      </div>
      {cert.aluno_curso && (
        <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-primary/10">
          <GraduationCap className="h-3.5 w-3.5 text-primary shrink-0" />
          <p className="text-helper text-text-secondary truncate">{cert.aluno_curso}</p>
        </div>
      )}
    </div>
  )
}

// ─── Detalhes do Certificado ──────────────────────────────────────────────────

function fmtHoras(v) {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  return Number.isNaN(n) ? '—' : `${n}h`
}

function fmtData(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function DetalhesCertificado({ cert }) {
  const [verOcr, setVerOcr] = useState(false)
  const horasDeclaradas = Number(cert.horas_declaradas)
  const horasOcr = cert.horas_validadas_ocr
  const divergente =
    horasDeclaradas > 0 && horasOcr != null && Number(horasOcr) > 0 &&
    Number(horasOcr) !== horasDeclaradas

  return (
    <div className="space-y-3">
      <div className="bg-bg rounded-sm border border-border">
        <MetaRow icon={FileText} label="Título da Atividade" value={cert.titulo_atividade || '—'} />
        <MetaRow icon={CalendarRange} label="Período de Realização" value={cert.periodo_realizacao || '—'} />
        <MetaRow icon={Layers} label="Eixo Formativo" value={cert.categoria_obj?.eixo || '—'} />
        <MetaRow icon={Hourglass} label="Horas Declaradas pelo Aluno" value={fmtHoras(cert.horas_declaradas)} />
        <MetaRow
          icon={Eye}
          label="Horas Lidas no PDF (OCR)"
          value={fmtHoras(horasOcr)}
          valueClass={divergente ? 'text-warning' : ''}
        />
        <MetaRow
          icon={cert.titularidade_confirmada ? ShieldCheck : AlertTriangle}
          label="Titularidade Documental"
          value={
            cert.titularidade_confirmada
              ? `Confirmada • ${Math.round(cert.similaridade_titularidade ?? 100)}%${cert.nome_extraido_ocr ? ` (${cert.nome_extraido_ocr})` : ''}`
              : `Divergente / Não identificado — Verificar PDF${cert.nome_extraido_ocr ? ` (Lido: ${cert.nome_extraido_ocr})` : ''}`
          }
          valueClass={cert.titularidade_confirmada ? 'text-success' : 'text-danger font-semibold'}
        />
      </div>

      {cert.titularidade_confirmada === false && (
        <div className="flex items-start gap-2 bg-danger-light/60 border border-danger-muted rounded-xs p-2.5 text-danger">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <p className="text-helper font-medium">
            Alerta de Titularidade (RN04): Nome do discente não identificado com clareza no documento{cert.nome_extraido_ocr ? ` (OCR extraiu "${cert.nome_extraido_ocr}")` : ''}. O envio requer revisão manual rigorosa da coordenação.
          </p>
        </div>
      )}

      {divergente && (
        <div className="flex items-start gap-2 bg-warning-light/60 border border-warning-muted rounded-xs p-2.5 text-yellow-700">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <p className="text-helper font-medium">
            O aluno declarou {horasDeclaradas}h, mas o OCR leu {Number(horasOcr)}h no documento. Confira o PDF.
          </p>
        </div>
      )}

      {cert.texto_extraido_ocr && (
        <div className="bg-bg rounded-sm border border-border">
          <button
            type="button"
            onClick={() => setVerOcr((v) => !v)}
            className="w-full flex items-center justify-between gap-2 px-3 py-2.5 text-helper font-semibold text-text-primary"
          >
            <span>Texto extraído do PDF (OCR)</span>
            <ChevronDown className={cn('h-4 w-4 transition-transform', verOcr && 'rotate-180')} />
          </button>
          {verOcr && (
            <pre className="px-3 pb-3 max-h-48 overflow-auto whitespace-pre-wrap break-words text-helper text-text-secondary font-sans border-t border-border pt-2">
              {cert.texto_extraido_ocr}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}


function BannerAvaliado({ cert }) {
  const isAprovado = cert.status === 'aprovado'

  if (isAprovado) {
    return (
      <div className="rounded-sm border-2 border-success bg-success-light p-5 space-y-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-success/20 flex items-center justify-center shrink-0">
            <BadgeCheck className="h-5 w-5 text-success" />
          </div>
          <div>
            <p className="text-label font-bold text-success">Documento Deferido</p>
            <p className="text-helper text-success/70">Avaliação registrada com sucesso.</p>
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

  // Rejeitado
  return (
    <div className="rounded-sm border-2 border-danger bg-danger-light p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-full bg-danger/20 flex items-center justify-center shrink-0">
          <MessageSquareX className="h-5 w-5 text-danger" />
        </div>
        <div>
          <p className="text-label font-bold text-danger">Documento Indeferido</p>
          <p className="text-helper text-danger/70">A justificativa foi registrada e é visível ao aluno.</p>
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

// ─── Ideia A: Resultado do SEBR com Rastro de Auditoria Textual ───────────────

function ResultadoSEBR({ resultado, horasEnviadas, categoriaObj }) {
  if (!resultado) return null
  const { horas_deferidas, horas_cortadas_evento, horas_cortadas_total, regra_aplicada } = resultado
  const teveCortesEv  = parseFloat(horas_cortadas_evento)  > 0
  const teveCortesTot = parseFloat(horas_cortadas_total)   > 0
  const teveCortess   = teveCortesEv || teveCortesTot

  // Mensagens de auditoria humanas
  const auditoria = []
  if (teveCortesEv) {
    const teto_ev = categoriaObj?.teto_por_evento
    auditoria.push(
      teto_ev != null
        ? `O SEBR cortou ${horas_cortadas_evento}h porque o limite por certificado desta categoria é de ${teto_ev}h.`
        : `O SEBR cortou ${horas_cortadas_evento}h pelo limite por evento desta categoria.`
    )
  }
  if (teveCortesTot) {
    const teto_tot = categoriaObj?.teto_total
    auditoria.push(
      teto_tot != null
        ? `Corte adicional de ${horas_cortadas_total}h por exceder o teto total de ${teto_tot}h permitidos nesta categoria.`
        : `Corte de ${horas_cortadas_total}h por atingir o teto total desta categoria.`
    )
  }

  return (
    <div className={cn(
      'rounded-sm border p-4 space-y-3',
      teveCortess
        ? 'bg-warning-light/50 border-warning-muted'
        : 'bg-success-light/50 border-success-muted',
    )}>
      <div className="flex items-center gap-2">
        <ShieldCheck className={cn('h-4 w-4', teveCortess ? 'text-yellow-600' : 'text-success')} />
        <p className={cn('text-label font-bold', teveCortess ? 'text-yellow-700' : 'text-success')}>
          {teveCortess ? 'Aprovado com Cortes Normativos' : 'Aprovado Integralmente'}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 text-helper">
        <div>
          <p className="text-text-secondary">Confirmado</p>
          <p className="font-semibold text-text-primary">{horasEnviadas}h</p>
        </div>
        <div>
          <p className="text-text-secondary">Deferido</p>
          <p className={cn('font-semibold', teveCortess ? 'text-yellow-700' : 'text-success')}>
            {horas_deferidas}h
          </p>
        </div>
      </div>

      {/* Ideia A: Rastro de Auditoria Textual */}
      {auditoria.length > 0 && (
        <div className="border-t border-warning-muted/60 pt-2.5 space-y-1.5">
          {auditoria.map((msg, i) => (
            <div key={i} className="flex items-start gap-2 text-yellow-700">
              <Scissors className="h-3.5 w-3.5 shrink-0 mt-0.5" />
              <p className="text-helper font-medium leading-relaxed">{msg}</p>
            </div>
          ))}
        </div>
      )}

      {/* Log técnico SEBR colapsado */}
      {regra_aplicada && (
        <p className="text-helper text-text-secondary italic border-t border-border/50 pt-2">
          {regra_aplicada}
        </p>
      )}
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────

export default function AvaliarCertificado() {
  const { id }     = useParams()
  const navigate   = useNavigate()

  const [cert,          setCert]          = useState(null)
  const [loading,       setLoading]       = useState(true)
  const [erro,          setErro]          = useState(null)

  const [horas,         setHoras]         = useState('')
  const [justificativa, setJustificativa] = useState('')
  const [submitting,    setSubmitting]    = useState(false)
  const [inputErro,     setInputErro]     = useState('')
  const [resultado,     setResultado]     = useState(null)

  // Ideia C: modal de regra
  const [modalRegra, setModalRegra] = useState(false)

  useEffect(() => {
    setLoading(true)
    certificadosService.obter(id)
      .then(({ data }) => {
        setCert(data)
        setHoras(data.horas_sugeridas_ia ?? '')
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

  // ── Aprovação ───────────────────────────────────────────────────────────────
  const handleAprovar = async () => {
    setInputErro('')
    if (!horas || Number(horas) <= 0) {
      setInputErro('Informe um valor de horas válido.')
      toast.error('Horas inválidas', { description: 'Por favor, informe as horas a deferir.' })
      return
    }
    try {
      setSubmitting(true)
      const { data } = await certificadosService.avaliar(id, {
        acao: 'aprovar',
        horas_confirmadas: parseFloat(horas),
      })
      setResultado(data)

      const deferidas   = parseFloat(data.horas_deferidas)
      const confirmadas = parseFloat(horas)
      if (deferidas < confirmadas) {
        const partes = []
        if (data.horas_cortadas_evento > 0) partes.push(`-${data.horas_cortadas_evento}h (evento)`)
        if (data.horas_cortadas_total  > 0) partes.push(`-${data.horas_cortadas_total}h (teto)`)
        toast.warning('Aprovado com cortes normativos!', {
          description: `SEBR deferiu ${deferidas}h de ${confirmadas}h. Cortes: ${partes.join(', ')}.`,
          duration: 7000,
        })
      } else {
        toast.success('Certificado aprovado!', { description: `${deferidas}h computadas.` })
      }

      const refreshed = await certificadosService.obter(id)
      setCert(refreshed.data)
    } catch (err) {
      const detail = err.response?.data?.detail || err?.data?.detail || err.friendlyMessage || 'Erro ao aprovar.'
      setInputErro(detail)
      toast.error('Erro na aprovação', { description: detail })
    } finally {
      setSubmitting(false)
    }
  }

  // ── Rejeição ────────────────────────────────────────────────────────────────
  const handleRejeitar = async () => {
    setInputErro('')
    if (!justificativa.trim()) {
      setInputErro('A justificativa é obrigatória para indeferimentos.')
      toast.error('Justificativa obrigatória', {
        description: 'Explique ao aluno o motivo do indeferimento.',
      })
      return
    }
    try {
      setSubmitting(true)
      await certificadosService.avaliar(id, {
        acao: 'rejeitar',
        justificativa: justificativa.trim(),
      })
      toast.success('Certificado indeferido.', {
        description: 'O aluno verá a justificativa no seu histórico.',
      })
      const refreshed = await certificadosService.obter(id)
      setCert(refreshed.data)
      setResultado(null)
    } catch (err) {
      const detail = err.response?.data?.detail || err?.data?.detail || err.friendlyMessage || 'Erro ao rejeitar.'
      setInputErro(detail)
      toast.error('Erro no indeferimento', { description: detail })
    } finally {
      setSubmitting(false)
    }
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
          onClick={() => navigate('/coordenador/revisao')}
          className="flex items-center gap-2 px-4 h-9 rounded-xs bg-primary text-white text-label font-medium"
        >
          <ArrowLeft className="h-4 w-4" /> Voltar à Fila
        </button>
      </div>
    )
  }

  const pdfUrl      = getPdfUrl(cert.arquivo_pdf)
  const statusCfg   = STATUS_CFG[cert.status] ?? STATUS_CFG.pendente_ocr
  const podeAvaliar = ['pendente_ocr', 'revisao_manual'].includes(cert.status)
  const dataEnvio   = cert.data_envio
    ? new Date(cert.data_envio).toLocaleString('pt-BR', {
        day: '2-digit', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : '—'

  return (
    <div className="min-h-screen bg-bg flex flex-col">

      {/* ── Ideia C: Modal de Regra ─────────────────────────────────────────── */}
      {modalRegra && cert.categoria_obj && (
        <ModalRegra regra={cert.categoria_obj} onClose={() => setModalRegra(false)} />
      )}

      {/* ── Barra de topo ─────────────────────────────────────────────────── */}
      <header className="h-16 bg-bg-surface border-b border-border flex items-center gap-4 px-4 shrink-0">
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

        <div className="ml-auto flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-primary" />
          <span className="text-helper font-medium text-text-secondary hidden sm:inline">
            Motor de Regras Ativo (SEBR)
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
            ║  DIREITA — Painel de Decisão SEBR    ║
            ╚══════════════════════════════════════╝ */}
        <aside className="w-96 shrink-0 flex flex-col overflow-y-auto bg-bg-surface">
          <div className="p-5 space-y-5">

            {/* 1. Identidade do Aluno */}
            <div>
              <SectionTitle>Aluno</SectionTitle>
              <CardAluno cert={cert} />
            </div>

            {/* 1b. Detalhes do Certificado */}
            <div>
              <SectionTitle>Dados do Certificado</SectionTitle>
              <DetalhesCertificado cert={cert} />
            </div>

            {/* 2. Ideia B: Termômetro de Categoria (com botão Ver Regra – Ideia C) */}
            <div>
              <SectionTitle>Contexto da Categoria</SectionTitle>
              <TermometroCategoriaCard
                cert={cert}
                onVerRegra={() => setModalRegra(true)}
              />
            </div>

            {/* 3. Análise da IA */}
            <div>
              <SectionTitle>Análise da IA</SectionTitle>
              <div className="bg-bg rounded-sm border border-border">
                <MetaRow icon={Calendar} label="Data de Envio" value={dataEnvio} />
                <MetaRow
                  icon={Hourglass}
                  label="Sugestão OCR"
                  value={cert.horas_sugeridas_ia != null ? `${cert.horas_sugeridas_ia}h` : '—'}
                  valueClass="text-primary"
                />
                <MetaRow
                  icon={Eye}
                  label="Confiança OCR"
                  value={cert.indice_confianca_ocr != null ? `${cert.indice_confianca_ocr}%` : '—'}
                  valueClass={Number(cert.indice_confianca_ocr) >= 70 ? 'text-success' : 'text-warning'}
                />
                <MetaRow
                  icon={cert.titularidade_confirmada ? ShieldCheck : AlertTriangle}
                  label="Titularidade Documental"
                  value={
                    cert.titularidade_confirmada
                      ? `Confirmada • ${Math.round(cert.similaridade_titularidade ?? 100)}%`
                      : 'Divergente / Não identificado — Verificar PDF'
                  }
                  valueClass={cert.titularidade_confirmada ? 'text-success' : 'text-danger font-semibold'}
                />
                {cert.horas_computadas_final != null && (
                  <MetaRow
                    icon={CheckCircle2}
                    label="Horas Computadas"
                    value={`${cert.horas_computadas_final}h`}
                    valueClass="text-success font-bold"
                  />
                )}
                {Number(cert.horas_descartadas) > 0 && (
                  <MetaRow
                    icon={TrendingDown}
                    label="Horas Descartadas"
                    value={`-${cert.horas_descartadas}h`}
                    valueClass="text-danger"
                  />
                )}
                <MetaRow
                  icon={Eye}
                  label="Confiança da IA"
                  value={(cert.confianca_ia ?? cert.indice_confianca_ocr) != null ? `${cert.confianca_ia ?? cert.indice_confianca_ocr}%` : '—'}
                  valueClass={Number(cert.confianca_ia ?? cert.indice_confianca_ocr) >= 70 ? 'text-success' : 'text-warning'}
                />
                <MetaRow icon={Clock} label="Última Atualização" value={fmtData(cert.data_atualizacao)} />
                <MetaRow icon={Hash} label="ID Interno" value={`#${cert.id}`} />
              </div>
            </div>

            {/* 4. Motivo do status (apenas pendentes) */}
            {cert.motivo_status && podeAvaliar && (
              <div className="flex items-start gap-2.5 bg-bg rounded-sm border border-border p-3">
                <Info className="h-4 w-4 text-text-secondary shrink-0 mt-0.5" />
                <p className="text-helper text-text-secondary">{cert.motivo_status}</p>
              </div>
            )}

            {/* 5. Ideia A: Resultado SEBR com Rastro Textual (após aprovação) */}
            {resultado && (
              <ResultadoSEBR
                resultado={resultado}
                horasEnviadas={parseFloat(horas)}
                categoriaObj={cert.categoria_obj}
              />
            )}

            {/* ════ ESTADO: pendente / revisão — Formulário de Decisão ════ */}
            {podeAvaliar && (
              <div>
                <SectionTitle>Decisão do Coordenador</SectionTitle>

                <div className="space-y-4">
                  <div>
                    <label className="text-helper font-semibold text-text-primary mb-1 block">
                      Horas a Deferir
                    </label>
                    <input
                      id="horas-input"
                      type="number"
                      step="0.5"
                      min="0"
                      value={horas}
                      onChange={(e) => setHoras(e.target.value)}
                      placeholder="Ex: 40"
                      className="w-full h-10 rounded-xs border border-border px-3 text-label focus:ring-2 focus:ring-primary outline-none bg-bg"
                    />
                    <p className="text-helper text-text-disabled mt-1">
                      O SEBR aplicará cortes normativos automaticamente.
                    </p>
                  </div>

                  <div>
                    <label className="text-helper font-semibold text-text-primary mb-1 block">
                      Justificativa{' '}
                      <span className="text-danger" title="Obrigatória em caso de indeferimento">*</span>
                    </label>
                    <textarea
                      id="justificativa-input"
                      value={justificativa}
                      onChange={(e) => setJustificativa(e.target.value)}
                      rows={4}
                      placeholder="Obrigatória em caso de indeferimento. Explique ao aluno o motivo."
                      className="w-full rounded-xs border border-border p-3 text-label focus:ring-2 focus:ring-primary outline-none resize-none bg-bg"
                    />
                  </div>

                  {inputErro && (
                    <div className="flex items-start gap-2 text-danger">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      <p className="text-helper">{inputErro}</p>
                    </div>
                  )}

                  <div className="flex gap-2 pt-1">
                    <button
                      id="btn-indeferir"
                      onClick={handleRejeitar}
                      disabled={submitting}
                      className="flex-1 h-10 rounded-xs border-2 border-danger text-danger font-semibold text-label hover:bg-danger hover:text-white transition-colors flex items-center justify-center gap-2"
                    >
                      {submitting
                        ? <Loader2 className="h-4 w-4 animate-spin" />
                        : <><XCircle className="h-4 w-4" /> Indeferir</>}
                    </button>
                    <button
                      id="btn-deferir"
                      onClick={handleAprovar}
                      disabled={submitting}
                      className="flex-1 h-10 rounded-xs bg-success text-white font-semibold text-label hover:bg-success/90 transition-colors flex items-center justify-center gap-2"
                    >
                      {submitting
                        ? <Loader2 className="h-4 w-4 animate-spin" />
                        : <><CheckCircle2 className="h-4 w-4" /> Deferir</>}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ════ ESTADO: Já Avaliado — Banner definitivo ════ */}
            {!podeAvaliar && <BannerAvaliado cert={cert} />}

          </div>
        </aside>
      </div>
    </div>
  )
}
