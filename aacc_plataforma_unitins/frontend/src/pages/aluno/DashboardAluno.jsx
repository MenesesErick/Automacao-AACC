import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText, CheckCircle, Clock, Award, AlertCircle,
  Plus, ChevronRight, TrendingUp
} from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { CertificadoDrawer } from '@/components/organisms/CertificadoDrawer'
import { certificadosService } from '@/services/api/endpoints'

// ── Mapa de status ───────────────────────────────────────────────────────────
const STATUS_MAP = {
  aprovado:            { label: 'Aprovado',       variant: 'success' },
  pendente_ocr:        { label: 'Pendente OCR',   variant: 'default' },
  revisao_manual:      { label: 'Revisão Manual', variant: 'warning' },
  rejeitado:           { label: 'Rejeitado',       variant: 'danger'  },
  requerimento_gerado: { label: 'Req. Gerado',    variant: 'primary' },
}

// ── Colunas da DataTable ─────────────────────────────────────────────────────
const COLUMNS = [
  {
    key: 'id',
    label: '#',
    render: (row) => (
      <span className="text-helper text-text-disabled font-mono">#{row.id}</span>
    ),
  },
  {
    key: 'categoria_nome',
    label: 'Categoria',
    render: (row) => (
      <div className="min-w-0">
        <p className="text-label font-medium text-text-primary truncate max-w-[180px]">
          {row.categoria_nome ?? '—'}
        </p>
      </div>
    ),
  },
  {
    key: 'horas',
    label: 'Horas',
    render: (row) => (
      <div className="text-right font-mono">
        <span className="text-label font-semibold text-text-primary">
          {row.horas_declaradas}h
        </span>
        {row.horas_computadas_final != null && (
          <p className="text-helper text-success">
            +{row.horas_computadas_final}h
          </p>
        )}
      </div>
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
    key: 'data_envio',
    label: 'Data',
    render: (row) =>
      row.data_envio
        ? new Date(row.data_envio).toLocaleDateString('pt-BR')
        : '—',
  },
  {
    key: 'action',
    label: '',
    render: () => (
      <ChevronRight className="h-4 w-4 text-text-disabled" />
    ),
  },
]

// ── Componente ───────────────────────────────────────────────────────────────
export default function DashboardAluno() {
  const [certificados, setCertificados]           = useState([])
  const [loading, setLoading]                     = useState(true)
  const [erro, setErro]                           = useState(null)
  const [certificadoSelecionado, setCertificado]  = useState(null)

  const fetchCertificados = useCallback(async () => {
    try {
      setLoading(true)
      setErro(null)
      const { data } = await certificadosService.listar()
      setCertificados(Array.isArray(data) ? data : (data.results ?? []))
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar certificados.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCertificados() }, [fetchCertificados])

  // ── KPIs ─────────────────────────────────────────────────────────────────
  const totalCerts     = certificados.length
  const horasAprovadas = certificados.reduce((a, c) => a + (c.horas_computadas_final ?? 0), 0)
  const pendentes      = certificados.filter(c => ['pendente_ocr', 'revisao_manual'].includes(c.status)).length
  const META            = 180
  const pct             = Math.min(Math.round((horasAprovadas / META) * 100), 100)

  return (
    <AppLayout
      breadcrumb={
        <div className="min-w-0">
          <p className="text-helper text-text-secondary">Portal do Aluno</p>
          <h1 className="text-h4 font-bold text-text-primary truncate">Meu Progresso AACC</h1>
        </div>
      }
    >
      {/* ── KPIs ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-5">
        <StatsCard
          title="Certificados"
          value={loading ? '…' : String(totalCerts)}
          icon={<FileText className="h-4 w-4" />}
          color="primary"
        />
        <StatsCard
          title="Horas Aprovadas"
          value={loading ? '…' : `${horasAprovadas}h`}
          icon={<CheckCircle className="h-4 w-4" />}
          color="success"
          trend="up"
          trendLabel={loading ? '' : `${pct}% da meta`}
        />
        <StatsCard
          title="Aguardando"
          value={loading ? '…' : String(pendentes)}
          icon={<Clock className="h-4 w-4" />}
          color="warning"
          subtitle="OCR + Revisão Manual"
        />
        <StatsCard
          title="Meta Total"
          value={`${META}h`}
          icon={<Award className="h-4 w-4" />}
          color="default"
          subtitle="Res. CONSUNI nº 057"
        />
      </div>

      {/* ── Barra de Progresso ───────────────────────────────────────── */}
      {!loading && (
        <div className="surface rounded-sm p-4 mb-5 flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between items-center mb-2">
              <span className="text-label font-semibold text-text-primary flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4 text-primary" />
                Progresso Geral
              </span>
              <span className="text-label font-bold text-primary tabular-nums">
                {horasAprovadas}h / {META}h
              </span>
            </div>
            <div className="h-2.5 bg-bg rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-700 ease-out"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="text-helper text-text-secondary mt-1.5">{pct}% da carga horária completada</p>
          </div>
          <Link
            to="/aluno/enviar"
            className="flex items-center gap-2 px-4 h-9 rounded-xs bg-primary text-white text-label font-medium hover:bg-primary-hover transition-colors shrink-0 shadow-xs"
          >
            <Plus className="h-4 w-4" />
            Enviar Certificado
          </Link>
        </div>
      )}

      {/* ── Tabela ───────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-card font-semibold text-text-primary">Histórico de Certificados</h2>
          <p className="text-helper text-text-secondary mt-0.5">
            Clique numa linha para ver detalhes e o documento.
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
          emptyLabel="Nenhum certificado enviado. Clique em 'Enviar Certificado' para começar."
          onRowClick={(row) => setCertificado(row)}
        />
      )}

      {/* ── Drawer ───────────────────────────────────────────────────── */}
      <CertificadoDrawer
        certificado={certificadoSelecionado}
        onClose={() => setCertificado(null)}
      />
    </AppLayout>
  )
}
