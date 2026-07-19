import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText, CheckCircle, Clock, Award, AlertCircle,
  Plus, ChevronRight, PartyPopper, TriangleAlert, Info
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadialBarChart, RadialBar,
  PolarAngleAxis
} from 'recharts'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { CertificadoDrawer } from '@/components/organisms/CertificadoDrawer'
import { certificadosService, alunoService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

// ── Design System cores (devem coincidir com tailwind.config.js) ─────────────
const CORES = {
  primary: '#0B5ED7',
  success: '#16A34A',
  warning: '#EAB308',
  danger:  '#DC2626',
  muted:   '#E5E7EB',
  text:    '#667085',
}

const COR_EIXO = {
  Ensino:   '#0B5ED7',
  Pesquisa: '#7C3AED',
  Extensao: '#16A34A',
}

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

// ── Tooltip customizado para o BarChart ──────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-border rounded-xs shadow-md px-3 py-2">
      <p className="text-helper font-semibold text-text-primary">{label}</p>
      <p className="text-label font-bold" style={{ color: payload[0]?.fill }}>
        {payload[0]?.value}h
      </p>
    </div>
  )
}

// ── Banner de Aptidão à Formatura ────────────────────────────────────────────
function BannerFormatura({ extrato, loading }) {
  if (loading) {
    return (
      <div className="surface rounded-sm p-4 mb-4 animate-pulse h-16" />
    )
  }
  if (!extrato) return null

  const { apto_formatura, faltam_horas, faltam_eixos } = extrato

  if (apto_formatura) {
    return (
      <div className="flex items-center gap-3 rounded-sm p-4 mb-4 bg-success-light border border-success-muted">
        <PartyPopper className="h-5 w-5 text-success shrink-0" />
        <div>
          <p className="text-label font-bold text-success">Parabéns! Você cumpriu todos os requisitos de AACC.</p>
          <p className="text-helper text-success/80 mt-0.5">
            Você pode solicitar a geração do Anexo I para entrega na Secretaria Acadêmica.
          </p>
        </div>
      </div>
    )
  }

  const partes = []
  if (faltam_horas > 0) partes.push(`${faltam_horas}h ainda`)
  if (faltam_eixos > 0) partes.push(`${faltam_eixos} eixo(s) a contemplar`)

  return (
    <div className="flex items-start gap-3 rounded-sm p-4 mb-4 bg-warning-light border border-warning-muted">
      <TriangleAlert className="h-5 w-5 text-warning shrink-0 mt-0.5" />
      <div>
        <p className="text-label font-bold text-yellow-700">Requisitos não cumpridos</p>
        <p className="text-helper text-yellow-600 mt-0.5">
          {partes.length > 0
            ? `Faltam ${partes.join(' e ')}. A formatura exige no mínimo 2 eixos distintos (Ensino, Pesquisa ou Extensão).`
            : 'Verifique as condições para formatura com seu coordenador.'}
        </p>
      </div>
    </div>
  )
}

// ── Gráfico Radial de Progresso ──────────────────────────────────────────────
function GraficoProgresso({ pct, horasAprovadas, meta }) {
  const data = [{ value: pct, fill: pct >= 100 ? CORES.success : CORES.primary }]
  return (
    <div className="surface rounded-sm p-5 flex flex-col items-center justify-center gap-2">
      <p className="text-helper text-text-disabled font-semibold uppercase tracking-wider self-start">
        Progresso Geral
      </p>
      <div className="relative w-full max-w-[180px] mx-auto" style={{ height: 180 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="50%"
            innerRadius="68%" outerRadius="90%"
            startAngle={90} endAngle={-270}
            data={data}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              dataKey="value"
              cornerRadius={6}
              background={{ fill: CORES.muted }}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        {/* Label central */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-h3 font-bold text-text-primary tabular-nums">{pct}%</span>
          <span className="text-helper text-text-secondary">{horasAprovadas}h / {meta}h</span>
        </div>
      </div>
    </div>
  )
}

// ── Gráfico de Barras por Eixo ───────────────────────────────────────────────
function GraficoEixos({ horas_por_eixo, meta }) {
  const data = Object.entries(horas_por_eixo ?? {}).map(([eixo, horas]) => ({
    eixo,
    horas,
    fill: COR_EIXO[eixo] ?? CORES.primary,
  }))

  return (
    <div className="surface rounded-sm p-5 flex flex-col gap-3 flex-1">
      <div className="flex items-center justify-between">
        <p className="text-helper text-text-disabled font-semibold uppercase tracking-wider">
          Horas por Eixo (RN02)
        </p>
        <div className="flex items-center gap-1 text-helper text-text-disabled">
          <Info className="h-3.5 w-3.5" />
          <span>≥ 2 eixos para formatura</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} barSize={36} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CORES.muted} vertical={false} />
          <XAxis
            dataKey="eixo"
            tick={{ fontSize: 12, fill: CORES.text }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: CORES.text }}
            axisLine={false}
            tickLine={false}
            domain={[0, Math.max(meta, ...Object.values(horas_por_eixo ?? {})) + 10]}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#F7F9FC' }} />
          <Bar dataKey="horas" radius={[6, 6, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legenda manual */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1">
        {data.map((d) => (
          <div key={d.eixo} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: d.fill }} />
            <span className="text-helper text-text-secondary">
              {d.eixo}: <strong className="text-text-primary">{d.horas}h</strong>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

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
