import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  X, User, Mail, Hash, BookOpen, FileText,
  ChevronRight, Loader2, AlertCircle
} from 'lucide-react'
import { Badge } from '@/components/atoms/Badge'
import { DataTable } from '@/components/organisms/DataTable'
import { BannerFormatura, GraficoProgresso, GraficoEixos } from '@/components/organisms/ExtratoCharts'
import { alunoService, certificadosService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

const STATUS_MAP = {
  aprovado:            { label: 'Aprovado',       variant: 'success' },
  pendente_ocr:        { label: 'Pendente OCR',   variant: 'default' },
  revisao_manual:      { label: 'Revisão Manual', variant: 'warning' },
  rejeitado:           { label: 'Rejeitado',      variant: 'danger'  },
  requerimento_gerado: { label: 'Req. Gerado',    variant: 'primary' },
}

const CERT_COLUMNS = [
  {
    key: 'id',
    label: '#',
    render: (r) => <span className="text-helper text-text-disabled font-mono">#{r.id}</span>,
  },
  {
    key: 'categoria_nome',
    label: 'Categoria',
    render: (r) => (
      <p className="text-label font-medium text-text-primary truncate max-w-[160px]">
        {r.categoria_nome ?? '—'}
      </p>
    ),
  },
  {
    key: 'horas',
    label: 'Horas',
    render: (r) => (
      <span className="text-label font-semibold tabular-nums">{r.horas_sugeridas_ia ?? r.horas_declaradas ?? 0}h</span>
    ),
  },
  {
    key: 'status',
    label: 'Status',
    render: (r) => {
      const s = STATUS_MAP[r.status] ?? { label: r.status, variant: 'default' }
      return <Badge variant={s.variant} dot>{s.label}</Badge>
    },
  },
  {
    key: 'data_envio',
    label: 'Data',
    render: (r) => r.data_envio ? new Date(r.data_envio).toLocaleDateString('pt-BR') : '—',
  },
]

function MetaItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2 text-label">
      <Icon className="h-4 w-4 text-text-secondary shrink-0" />
      <span className="text-text-secondary">{label}:</span>
      <span className="font-semibold text-text-primary">{value}</span>
    </div>
  )
}

export function AlunoRaioXDrawer({ aluno, onClose }) {
  const [extrato,  setExtrato]  = useState(null)
  const [certs,    setCerts]    = useState([])
  const [loading,  setLoading]  = useState(false)
  const [erro,     setErro]     = useState(null)

  // Fechar com Escape
  useEffect(() => {
    if (!aluno) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [aluno, onClose])

  // Bloquear scroll
  useEffect(() => {
    document.body.style.overflow = aluno ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [aluno])

  // Buscar dados quando um aluno é selecionado
  useEffect(() => {
    if (!aluno) return
    let cancelled = false

    const fetchDados = async () => {
      setLoading(true)
      setErro(null)
      setExtrato(null)
      setCerts([])
      try {
        const [resExtrato, resCerts] = await Promise.all([
          alunoService.obterExtrato(aluno.id),
          certificadosService.listar(),
        ])
        if (!cancelled) {
          setExtrato(resExtrato.data)
          const allCerts = Array.isArray(resCerts.data)
            ? resCerts.data
            : (resCerts.data.results ?? [])
          // O coordenador vê todos — filtramos pelo aluno pelo campo 'aluno' (id do perfil)
          setCerts(allCerts.filter(c => c.aluno === aluno.id))
        }
      } catch (err) {
        if (!cancelled) setErro(err.friendlyMessage ?? 'Erro ao carregar dados do aluno.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchDados()
    return () => { cancelled = true }
  }, [aluno])

  if (!aluno) return null

  const pct   = extrato?.progresso_percentual  ?? 0
  const total = extrato?.total_horas_aprovadas ?? 0
  const meta  = extrato?.meta_horas            ?? 180

  const content = (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside
        className="fixed top-0 right-0 z-50 h-screen w-full max-w-3xl flex flex-col bg-bg-surface border-l border-border shadow-2xl animate-drawer-in"
        role="dialog"
        aria-modal="true"
      >
        {/* Cabeçalho */}
        <header className="flex items-start gap-4 px-6 py-4 border-b border-border shrink-0">
          <div className="h-10 w-10 rounded-xs bg-primary-light flex items-center justify-center shrink-0">
            <User className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-h4 font-bold text-text-primary leading-tight truncate">
              {aluno.aluno_nome}
            </h2>
            <p className="text-helper text-text-secondary">Raio-X AACC</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xs text-text-secondary hover:text-text-primary hover:bg-bg transition-colors shrink-0"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        {/* Meta do aluno */}
        <div className="px-6 py-3 border-b border-border bg-bg flex flex-wrap gap-x-5 gap-y-1.5 shrink-0">
          <MetaItem icon={Hash}     label="Matrícula" value={aluno.matricula} />
          <MetaItem icon={Mail}     label="Email"     value={aluno.email} />
          <MetaItem icon={BookOpen} label="Curso"     value={aluno.curso} />
          <MetaItem icon={FileText} label="Certs"     value={`${aluno.total_certs} enviados`} />
        </div>

        {/* Corpo scrollável */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center h-40 gap-3 text-text-secondary">
              <Loader2 className="h-5 w-5 animate-spin" />
              <p className="text-label">Carregando dados do aluno...</p>
            </div>
          ) : erro ? (
            <div className="flex items-center gap-3 text-danger surface rounded-sm p-4">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p className="text-label">{erro}</p>
            </div>
          ) : (
            <>
              {/* Banner de Formatura */}
              <BannerFormatura extrato={extrato} loading={false} />

              {/* Gráficos lado a lado */}
              <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-3">
                <GraficoProgresso pct={pct} horasAprovadas={total} meta={meta} />
                <GraficoEixos horas_por_eixo={extrato?.horas_por_eixo} meta={meta} />
              </div>

              {/* Lista de Certificados */}
              <div>
                <p className="text-helper text-text-disabled font-semibold uppercase tracking-wider mb-2">
                  Histórico de Certificados ({certs.length})
                </p>
                <DataTable
                  columns={CERT_COLUMNS}
                  data={certs}
                  loading={false}
                  emptyLabel="Este aluno ainda não enviou nenhum certificado."
                />
              </div>
            </>
          )}
        </div>
      </aside>
    </>
  )

  return createPortal(content, document.body)
}
