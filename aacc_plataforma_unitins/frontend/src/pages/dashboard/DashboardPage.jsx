import { FileText, CheckCircle, Clock, Award } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'

const STATUS_MAP = {
  aprovado:            { label: 'Aprovado',        variant: 'success' },
  pendente_ocr:        { label: 'Pendente OCR',    variant: 'warning' },
  revisao_manual:      { label: 'Revisão Manual',  variant: 'danger'  },
  rejeitado:           { label: 'Rejeitado',        variant: 'default' },
  requerimento_gerado: { label: 'Req. Gerado',     variant: 'primary' },
}

const MOCK_CERTIFICADOS = [
  { id: 1, categoria: 'Iniciação científica', horas_declaradas: '60', horas_computadas_final: 60, status: 'aprovado',       data_envio: '2026-07-01' },
  { id: 2, categoria: 'Monitoria voluntária', horas_declaradas: '40', horas_computadas_final: 40, status: 'pendente_ocr',   data_envio: '2026-07-05' },
  { id: 3, categoria: 'Cursos de extensão',   horas_declaradas: '80', horas_computadas_final: 40, status: 'revisao_manual', data_envio: '2026-07-10' },
]

const COLUMNS = [
  { key: 'id',       label: '#' },
  { key: 'categoria', label: 'Categoria' },
  { key: 'horas_declaradas',    label: 'Declaradas' },
  { key: 'horas_computadas_final', label: 'Aprovadas' },
  {
    key: 'status',
    label: 'Status',
    render: (row) => {
      const s = STATUS_MAP[row.status] ?? { label: row.status, variant: 'default' }
      return <Badge variant={s.variant} dot>{s.label}</Badge>
    },
  },
  { key: 'data_envio', label: 'Data' },
]

export default function DashboardPage() {
  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Bem-vindo de volta 👋</p>
          <h1 className="text-h3 font-bold text-text-primary">Dashboard</h1>
        </div>
      }
    >
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatsCard
          title="Total de Certificados"
          value="24"
          icon={<FileText className="h-4 w-4" />}
          color="primary"
          trend="up"
          trendLabel="+3 este mês"
        />
        <StatsCard
          title="Horas Aprovadas"
          value="148h"
          icon={<CheckCircle className="h-4 w-4" />}
          color="success"
          trend="up"
          trendLabel="82% da meta"
        />
        <StatsCard
          title="Pendentes de Revisão"
          value="3"
          icon={<Clock className="h-4 w-4" />}
          color="warning"
          trend="down"
          trendLabel="-2 vs. semana anterior"
        />
        <StatsCard
          title="Meta Total (Matriz)"
          value="180h"
          icon={<Award className="h-4 w-4" />}
          color="default"
          subtitle="Sistemas de Informação 2022"
        />
      </div>

      {/* Últimos Certificados */}
      <div className="mb-2">
        <h2 className="text-card font-semibold text-text-primary">Últimos Certificados</h2>
        <p className="text-label text-text-secondary mt-0.5">Submissões recentes e status do motor de regras.</p>
      </div>
      <DataTable columns={COLUMNS} data={MOCK_CERTIFICADOS} />
    </AppLayout>
  )
}
