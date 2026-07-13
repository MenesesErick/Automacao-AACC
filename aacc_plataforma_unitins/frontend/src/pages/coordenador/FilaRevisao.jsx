import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { Button } from '@/components/atoms/Button'
import { Eye, CheckCircle, XCircle } from 'lucide-react'

const MOCK_FILA = [
  { 
    id: 101, 
    aluno: 'Maria Souza (SI)', 
    categoria: 'Participação em Congresso', 
    horas_declaradas: 40,
    confianca: 62.5,
    motivo: 'Índice de confiança OCR abaixo do limiar',
    data: '2026-07-13'
  },
  { 
    id: 102, 
    aluno: 'Pedro Santos (Agro)', 
    categoria: 'Estágio Extracurricular', 
    horas_declaradas: 120,
    confianca: 55.0,
    motivo: 'Assinatura ilegível no PDF',
    data: '2026-07-12'
  },
]

const COLUMNS = [
  { key: 'aluno', label: 'Aluno / Curso' },
  { key: 'categoria', label: 'Categoria' },
  { key: 'horas_declaradas', label: 'Carga Horária' },
  { 
    key: 'confianca', 
    label: 'Confiança OCR',
    render: (row) => (
      <Badge variant="danger" dot>{row.confianca}%</Badge>
    )
  },
  { key: 'motivo', label: 'Motivo da Retenção' },
  {
    key: 'acoes',
    label: 'Ações',
    render: () => (
      <div className="flex items-center gap-2">
        <Button size="xs" variant="secondary" leftIcon={<Eye className="h-3 w-3" />}>Ver Doc</Button>
        <Button size="xs" variant="success" leftIcon={<CheckCircle className="h-3 w-3" />}>Aprovar</Button>
        <Button size="xs" variant="danger" leftIcon={<XCircle className="h-3 w-3" />}>Recusar</Button>
      </div>
    )
  }
]

export default function FilaRevisao() {
  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Coordenação / Auditoria</p>
          <h1 className="text-h3 font-bold text-text-primary">Fila de Revisão Manual</h1>
        </div>
      }
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-card font-semibold text-text-primary">Certificados Retidos</h2>
          <p className="text-label text-text-secondary mt-0.5">Documentos que não atingiram a confiança mínima do OCR (RN04).</p>
        </div>
      </div>
      
      <DataTable columns={COLUMNS} data={MOCK_FILA} />
    </AppLayout>
  )
}
