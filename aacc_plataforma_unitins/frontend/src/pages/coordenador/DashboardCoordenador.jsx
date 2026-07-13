import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { ShieldAlert, Users, CheckCircle, FileWarning } from 'lucide-react'

export default function DashboardCoordenador() {
  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Visão Geral da Coordenação</p>
          <h1 className="text-h3 font-bold text-text-primary">Dashboard</h1>
        </div>
      }
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatsCard
          title="Fila de Revisão"
          value="12"
          icon={<ShieldAlert className="h-4 w-4" />}
          color="danger"
          trend="up"
          trendLabel="+4 submissões"
          subtitle="Baixa confiança OCR"
        />
        <StatsCard
          title="Aprovações Automáticas"
          value="85%"
          icon={<CheckCircle className="h-4 w-4" />}
          color="success"
          trend="up"
          trendLabel="+2% esta semana"
        />
        <StatsCard
          title="Alunos Ativos"
          value="240"
          icon={<Users className="h-4 w-4" />}
          color="primary"
        />
        <StatsCard
          title="Horas Descartadas"
          value="450h"
          icon={<FileWarning className="h-4 w-4" />}
          color="warning"
          subtitle="Por teto máximo da matriz"
        />
      </div>

      <div className="surface rounded-sm p-6 text-center text-text-secondary">
        <p className="text-label font-medium mb-1">Estatísticas detalhadas em breve</p>
        <p className="text-helper">Os gráficos de desempenho de aprovação e distribuição de eixos serão inseridos aqui.</p>
      </div>
    </AppLayout>
  )
}
