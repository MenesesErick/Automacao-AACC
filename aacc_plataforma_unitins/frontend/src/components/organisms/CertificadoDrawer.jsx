import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import {
  X, FileText, Clock, CheckCircle2, XCircle,
  AlertTriangle, Eye, Download, Calendar, Hash,
  Layers, Hourglass, TrendingDown, Info
} from 'lucide-react'
import { Badge } from '@/components/atoms/Badge'
import { cn } from '@/utils/cn'

// ── Mapa de status → Badge + ícone + texto ──────────────────────────────────
const STATUS_CONFIG = {
  aprovado: {
    label: 'Aprovado',
    variant: 'success',
    Icon: CheckCircle2,
    bannerClass: 'bg-success-light border-success-muted text-success',
  },
  rejeitado: {
    label: 'Rejeitado',
    variant: 'danger',
    Icon: XCircle,
    bannerClass: 'bg-danger-light border-danger-muted text-danger',
  },
  revisao_manual: {
    label: 'Revisão Manual',
    variant: 'warning',
    Icon: AlertTriangle,
    bannerClass: 'bg-warning-light border-warning-muted text-yellow-700',
  },
  pendente_ocr: {
    label: 'Pendente OCR',
    variant: 'default',
    Icon: Clock,
    bannerClass: 'bg-bg border-border text-text-secondary',
  },
  requerimento_gerado: {
    label: 'Req. Gerado',
    variant: 'primary',
    Icon: FileText,
    bannerClass: 'bg-primary-light border-primary-muted text-primary',
  },
}

function MetaRow({ icon: Icon, label, value, valueClass = '' }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-border last:border-0">
      <div className="h-8 w-8 rounded-xs bg-bg flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="h-4 w-4 text-text-secondary" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-helper text-text-secondary">{label}</p>
        <p className={cn('text-label font-semibold text-text-primary mt-0.5 break-words', valueClass)}>
          {value ?? '—'}
        </p>
      </div>
    </div>
  )
}

export function CertificadoDrawer({ certificado, onClose }) {
  // Fechar com Escape
  useEffect(() => {
    if (!certificado) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [certificado, onClose])

  // Bloquear scroll do body enquanto aberto
  useEffect(() => {
    document.body.style.overflow = certificado ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [certificado])

  if (!certificado) return null

  const cfg = STATUS_CONFIG[certificado.status] ?? STATUS_CONFIG.pendente_ocr
  const { label, variant, Icon: StatusIcon, bannerClass } = cfg

  const pdfUrl = certificado.arquivo_pdf
    ? (certificado.arquivo_pdf.startsWith('http')
      ? certificado.arquivo_pdf
      : `/media/${certificado.arquivo_pdf}`)
    : null

  const dataEnvio = certificado.data_envio
    ? new Date(certificado.data_envio).toLocaleDateString('pt-BR', {
        day: '2-digit', month: 'long', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      })
    : '—'

  const content = (
    <>
      {/* ── Overlay ───────────────────────────────────────────────────── */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* ── Drawer Panel ──────────────────────────────────────────────── */}
      <aside
        className={cn(
          'fixed top-0 right-0 z-50 h-screen',
          'w-full max-w-3xl flex flex-col',
          'bg-bg-surface border-l border-border shadow-2xl',
          'animate-drawer-in',
        )}
        role="dialog"
        aria-modal="true"
        aria-label={`Detalhes do certificado ${certificado.id}`}
      >
        {/* ── Cabeçalho ────────────────────────────────────────────── */}
        <header className="flex items-start gap-4 px-6 py-4 border-b border-border shrink-0">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-helper text-text-secondary font-medium">Certificado #{certificado.id}</span>
              <Badge variant={variant} dot>{label}</Badge>
            </div>
            <h2 className="text-h4 font-bold text-text-primary leading-snug line-clamp-1">
              {certificado.categoria_nome ?? 'Categoria'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xs text-text-secondary hover:text-text-primary hover:bg-bg transition-colors shrink-0"
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {/* ── Banner de Motivo (quando relevante) ─────────────────── */}
        {certificado.motivo_status && certificado.status !== 'aprovado' && (
          <div className={cn('flex items-start gap-3 px-6 py-3 border-b border-border', bannerClass)}>
            <Info className="h-4 w-4 shrink-0 mt-0.5" />
            <p className="text-label">{certificado.motivo_status}</p>
          </div>
        )}

        {/* ── Corpo ────────────────────────────────────────────────── */}
        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row min-h-0">

          {/* Coluna Esquerda — Metadados */}
          <div className="lg:w-72 lg:shrink-0 overflow-y-auto px-6 py-4 border-b lg:border-b-0 lg:border-r border-border">
            <p className="text-helper text-text-disabled font-semibold uppercase tracking-wider mb-2">
              Detalhes da Submissão
            </p>

            <MetaRow icon={Layers}    label="Categoria"          value={certificado.categoria_nome} />
            <MetaRow icon={Calendar}  label="Data de Envio"      value={dataEnvio} />
            <MetaRow
              icon={Hourglass}
              label="Horas Declaradas"
              value={`${certificado.horas_declaradas}h`}
            />
            <MetaRow
              icon={CheckCircle2}
              label="Horas Aprovadas"
              value={certificado.horas_computadas_final != null ? `${certificado.horas_computadas_final}h` : 'Pendente'}
              valueClass={certificado.horas_computadas_final > 0 ? 'text-success' : ''}
            />
            {certificado.horas_descartadas > 0 && (
              <MetaRow
                icon={TrendingDown}
                label="Horas Descartadas"
                value={`-${certificado.horas_descartadas}h`}
                valueClass="text-danger"
              />
            )}
            {certificado.indice_confianca_ocr != null && (
              <MetaRow
                icon={Eye}
                label="Confiança OCR"
                value={`${certificado.indice_confianca_ocr}%`}
                valueClass={
                  Number(certificado.indice_confianca_ocr) >= 70
                    ? 'text-success'
                    : 'text-warning'
                }
              />
            )}
            <MetaRow icon={Hash} label="ID Interno" value={`#${certificado.id}`} />

            {/* Status visual */}
            <div className={cn(
              'mt-4 rounded-sm p-3 flex items-center gap-3 border',
              bannerClass,
            )}>
              <StatusIcon className="h-5 w-5 shrink-0" />
              <div>
                <p className="text-label font-semibold">{label}</p>
                {certificado.motivo_status && (
                  <p className="text-helper opacity-80 mt-0.5">{certificado.motivo_status}</p>
                )}
              </div>
            </div>
          </div>

          {/* Coluna Direita — Preview do PDF */}
          <div className="flex-1 flex flex-col min-h-0 p-4 bg-bg overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <p className="text-helper text-text-disabled font-semibold uppercase tracking-wider">
                Documento Anexado
              </p>
              {pdfUrl && (
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  download
                  className="flex items-center gap-1.5 text-helper text-primary hover:underline font-medium"
                >
                  <Download className="h-3.5 w-3.5" />
                  Abrir / Baixar
                </a>
              )}
            </div>

            {pdfUrl ? (
              <iframe
                src={pdfUrl}
                title={`PDF Certificado #${certificado.id}`}
                className="flex-1 rounded-sm border border-border w-full min-h-0 bg-white"
                style={{ minHeight: 300 }}
              />
            ) : (
              <div className="flex-1 rounded-sm border border-border bg-bg flex flex-col items-center justify-center text-center p-8 gap-3">
                <FileText className="h-10 w-10 text-text-disabled" />
                <p className="text-label text-text-secondary font-medium">Nenhum documento disponível</p>
                <p className="text-helper text-text-disabled">O arquivo ainda está sendo processado.</p>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )

  return createPortal(content, document.body)
}
