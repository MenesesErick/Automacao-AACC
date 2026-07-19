import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText, CheckCircle, Clock, Award, AlertCircle,
  Plus, ChevronRight
} from 'lucide-react'

import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { CertificadoDrawer } from '@/components/organisms/CertificadoDrawer'
import { certificadosService, alunoService } from '@/services/api/endpoints'
import { BannerFormatura, GraficoProgresso, GraficoEixos } from '@/components/organisms/ExtratoCharts'
import { cn } from '@/utils/cn'



// ── Mapa de status ─────────────────────────────────────────────────────────
const STATUS_MAP = {
  aprovado:            { label: 'Aprovado',       variant: 'success' },
  pendente_ocr:        { label: 'Pendente OCR',   variant: 'default' },
  revisao_manual:      { label: 'Revisão Manual', variant: 'warning' },
  rejeitado:           { label: 'Rejeitado',      variant: 'danger'  },
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
      <p className="text-label font-medium text-text-primary truncate max-w-[180px]">
        {row.categoria_nome ?? '—'}
      </p>
    ),
  },
  {
    key: 'horas',
    label: 'Horas',
    render: (row) => (
      <div className="text-right font-mono">
        <span className="text-label font-semibold text-text-primary">{row.horas_declaradas}h</span>
        {row.horas_computadas_final != null && (
          <p className="text-helper text-success">+{row.horas_computadas_final}h</p>
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
      row.data_envio ? new Date(row.data_envio).toLocaleDateString('pt-BR') : '—',
  },
  {
    key: 'action',
    label: '',
    render: () => <ChevronRight className="h-4 w-4 text-text-disabled" />,
  },
]



// ── Componente Principal ─────────────────────────────────────────────────────
export default function DashboardAluno() {
  const [certificados, setCertificados]          = useState([])
  const [extrato, setExtrato]                    = useState(null)
  const [loadingCerts, setLoadingCerts]          = useState(true)
  const [loadingExtrato, setLoadingExtrato]      = useState(true)
  const [erro, setErro]                          = useState(null)
  const [certificadoSelecionado, setCertificado] = useState(null)

  const fetchCertificados = useCallback(async () => {
    try {
      setLoadingCerts(true)
      const { data } = await certificadosService.listar()
      setCertificados(Array.isArray(data) ? data : (data.results ?? []))
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar certificados.')
    } finally {
      setLoadingCerts(false)
    }
  }, [])

  const fetchExtrato = useCallback(async () => {
    try {
      setLoadingExtrato(true)
      const { data } = await alunoService.obterMeuExtrato()
      setExtrato(data)
    } catch {
      // Falha silenciosa — KPIs ficam zerados mas não bloqueia a tela
    } finally {
      setLoadingExtrato(false)
    }
  }, [])

  useEffect(() => {
    fetchCertificados()
    fetchExtrato()
  }, [fetchCertificados, fetchExtrato])

  // Dados do extrato (com fallback safe)
  const total      = extrato?.total_horas_aprovadas ?? 0
  const meta       = extrato?.meta_horas           ?? 180
  const pct        = extrato?.progresso_percentual  ?? 0
  const pendentes  = certificados.filter(c => ['pendente_ocr','revisao_manual'].includes(c.status)).length
  const totalCerts = certificados.length

  return (
    <AppLayout
      breadcrumb={
        <div className="min-w-0">
          <p className="text-helper text-text-secondary">Portal do Aluno</p>
          <h1 className="text-h4 font-bold text-text-primary truncate">Meu Progresso AACC</h1>
        </div>
      }
    >
      {/* ── Banner de formatura ─────────────────────────────────────────── */}
      <BannerFormatura extrato={extrato} loading={loadingExtrato} />

      {/* ── KPIs ────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-4">
        <StatsCard
          title="Certificados"
          value={loadingCerts ? '…' : String(totalCerts)}
          icon={<FileText className="h-4 w-4" />}
          color="primary"
        />
        <StatsCard
          title="Horas Aprovadas"
          value={loadingExtrato ? '…' : `${total}h`}
          icon={<CheckCircle className="h-4 w-4" />}
          color="success"
          trend={pct > 0 ? 'up' : 'neutral'}
          trendLabel={`${pct}% da meta`}
        />
        <StatsCard
          title="Em Análise"
          value={loadingCerts ? '…' : String(pendentes)}
          icon={<Clock className="h-4 w-4" />}
          color="warning"
          subtitle="OCR + Revisão Manual"
        />
        <StatsCard
          title="Meta AACC"
          value={`${meta}h`}
          icon={<Award className="h-4 w-4" />}
          color="default"
          subtitle="Res. CONSUNI nº 057"
        />
      </div>

      {/* ── Gráficos ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-3 mb-4">
        {loadingExtrato ? (
          <>
            <div className="surface rounded-sm h-64 animate-pulse" />
            <div className="surface rounded-sm h-64 animate-pulse" />
          </>
        ) : (
          <>
            <GraficoProgresso pct={pct} horasAprovadas={total} meta={meta} />
            <GraficoEixos horas_por_eixo={extrato?.horas_por_eixo} meta={meta} />
          </>
        )}
      </div>

      {/* ── Ação principal ──────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-card font-semibold text-text-primary">Histórico de Certificados</h2>
          <p className="text-helper text-text-secondary mt-0.5">
            Clique numa linha para ver detalhes e o documento.
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

      {/* ── Tabela ──────────────────────────────────────────────────────── */}
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
          loading={loadingCerts}
          emptyLabel="Nenhum certificado enviado. Clique em 'Enviar Certificado' para começar."
          onRowClick={(row) => setCertificado(row)}
        />
      )}

      {/* ── Drawer ──────────────────────────────────────────────────────── */}
      <CertificadoDrawer
        certificado={certificadoSelecionado}
        onClose={() => setCertificado(null)}
      />
    </AppLayout>
  )
}
