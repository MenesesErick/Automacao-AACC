import { useState, useEffect, useCallback } from 'react'
import { FileText, CheckCircle, Clock, Award, AlertCircle } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { certificadosService } from '@/services/api/endpoints'
import { useAuth } from '@/contexts/AuthContext'

const STATUS_MAP = {
  aprovado:            { label: 'Aprovado',       variant: 'success' },
  pendente_ocr:        { label: 'Pendente OCR',   variant: 'warning' },
  revisao_manual:      { label: 'Revisão Manual', variant: 'danger'  },
  rejeitado:           { label: 'Rejeitado',       variant: 'default' },
  requerimento_gerado: { label: 'Req. Gerado',    variant: 'primary' },
}

const COLUMNS = [
  { key: 'id', label: '#' },
  {
    key: 'categoria_nome',
    label: 'Categoria',
    render: (row) => <span className="text-label text-text-primary">{row.categoria_nome ?? '—'}</span>,
  },
  {
    key: 'horas_declaradas',
    label: 'Declaradas',
    render: (row) => <span className="font-medium">{row.horas_declaradas}h</span>,
  },
  {
    key: 'horas_computadas_final',
    label: 'Aprovadas',
    render: (row) => (
      <span className={row.horas_descartadas > 0 ? 'text-warning font-semibold' : 'font-semibold'}>
        {row.horas_computadas_final ?? '—'}h
      </span>
    ),
  },
  {
    key: 'horas_descartadas',
    label: 'Descartadas',
    render: (row) =>
      row.horas_descartadas > 0 ? (
        <span className="text-danger font-medium">-{row.horas_descartadas}h</span>
      ) : (
        <span className="text-text-disabled">—</span>
      ),
  },
  {
    key: 'status',
    label: 'Status',
    render: (row) => {
      const s = STATUS_MAP[row.status] ?? { label: row.status, variant: 'default' }
      return <Badge variant={s.variant} dot>{s.label}</Badge>
    },
  },
  {
    key: 'motivo_status',
    label: 'Motivo',
    render: (row) => (
      <span className="text-helper text-text-secondary max-w-xs truncate block" title={row.motivo_status}>
        {row.motivo_status ?? '—'}
      </span>
    ),
  },
  {
    key: 'data_envio',
    label: 'Data de Envio',
    render: (row) =>
      row.data_envio
        ? new Date(row.data_envio).toLocaleDateString('pt-BR')
        : '—',
  },
]

export default function DashboardAluno() {
  const { user } = useAuth()
  const [certificados, setCertificados] = useState([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState(null)

  const fetchCertificados = useCallback(async () => {
    try {
      setLoading(true)
      setErro(null)
      const { data } = await certificadosService.listar()
      // A API pode retornar lista direta ou {results: [...]} (DRF pagination)
      setCertificados(Array.isArray(data) ? data : (data.results ?? []))
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar certificados.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCertificados()
  }, [fetchCertificados])

  // ── KPIs calculados a partir dos dados reais ─────────────────────────────
  const totalCertificados  = certificados.length
  const horasAprovadas     = certificados.reduce((acc, c) => acc + (c.horas_computadas_final ?? 0), 0)
  const horasDescartadas   = certificados.reduce((acc, c) => acc + (c.horas_descartadas ?? 0), 0)
  const pendentes          = certificados.filter(
    (c) => c.status === 'pendente_ocr' || c.status === 'revisao_manual'
  ).length

  const META_HORAS = 180 // Resolução 057 — matriz padrão
  const pctMeta = Math.min(Math.round((horasAprovadas / META_HORAS) * 100), 100)

  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Portal do Aluno</p>
          <h1 className="text-h3 font-bold text-text-primary">Meu Progresso AACC</h1>
        </div>
      }
    >
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatsCard
          title="Total de Certificados"
          value={loading ? '…' : String(totalCertificados)}
          icon={<FileText className="h-4 w-4" />}
          color="primary"
        />
        <StatsCard
          title="Horas Aprovadas"
          value={loading ? '…' : `${horasAprovadas}h`}
          icon={<CheckCircle className="h-4 w-4" />}
          color="success"
          trendLabel={loading ? '' : `${pctMeta}% da meta`}
          trend="up"
        />
        <StatsCard
          title="Aguardando Revisão"
          value={loading ? '…' : String(pendentes)}
          icon={<Clock className="h-4 w-4" />}
          color="warning"
          subtitle="Pendente OCR + Revisão Manual"
        />
        <StatsCard
          title="Meta Total (Matriz)"
          value={`${META_HORAS}h`}
          icon={<Award className="h-4 w-4" />}
          color="default"
          subtitle="Resolução CONSUNI nº 057"
        />
      </div>

      {/* Barra de progresso */}
      {!loading && (
        <div className="surface rounded-sm p-4 mb-6 flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-label font-medium text-text-primary">Progresso Geral AACC</span>
              <span className="text-label font-bold text-primary">{horasAprovadas}h / {META_HORAS}h</span>
            </div>
            <div className="h-2 bg-bg rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${pctMeta}%` }}
              />
            </div>
            {horasDescartadas > 0 && (
              <p className="text-helper text-text-secondary mt-1.5">
                <span className="text-warning font-medium">{horasDescartadas}h descartadas</span>
                {' '}por atingir o teto da categoria (Res. 057).
              </p>
            )}
          </div>
        </div>
      )}

      {/* Tabela de Certificados */}
      <div className="mb-2 flex items-center justify-between">
        <div>
          <h2 className="text-card font-semibold text-text-primary">Histórico de Certificados</h2>
          <p className="text-label text-text-secondary mt-0.5">
            Submissões e status do motor de regras.
          </p>
        </div>
      </div>

      {erro ? (
        <div className="surface rounded-sm p-6 flex items-center gap-3 text-danger">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="text-label font-semibold">Erro ao carregar dados</p>
            <p className="text-helper text-text-secondary mt-0.5">{erro}</p>
          </div>
        </div>
      ) : (
        <DataTable
          columns={COLUMNS}
          data={certificados}
          loading={loading}
          emptyLabel="Nenhum certificado enviado ainda. Que tal enviar o primeiro?"
        />
      )}
    </AppLayout>
  )
}
