import { useState, useEffect, useCallback } from 'react'
import {
  ShieldCheck, AlertCircle, Search, Filter, ChevronRight
} from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { CertificadoDrawer } from '@/components/organisms/CertificadoDrawer'
import { certificadosService } from '@/services/api/endpoints'

const STATUS_MAP = {
  pendente_ocr:        { label: 'Pendente OCR',   variant: 'default' },
  revisao_manual:      { label: 'Revisão Manual', variant: 'warning' },
}

const COLUMNS = [
  {
    key: 'id',
    label: '#',
    render: (row) => (
      <span className="text-helper text-text-disabled font-mono">#{row.id}</span>
    ),
  },
  {
    key: 'aluno',
    label: 'Aluno',
    render: (row) => (
      <div className="min-w-0">
        <p className="text-label font-medium text-text-primary truncate max-w-[150px]">
          Matrícula {row.aluno}
        </p>
      </div>
    ),
  },
  {
    key: 'categoria_nome',
    label: 'Categoria',
    render: (row) => (
      <div className="min-w-0">
        <p className="text-label font-medium text-text-primary truncate max-w-[200px]">
          {row.categoria_nome ?? '—'}
        </p>
      </div>
    ),
  },
  {
    key: 'horas',
    label: 'Sugestão IA',
    render: (row) => (
      <span className="text-label font-semibold text-text-primary font-mono">
        {row.horas_sugeridas_ia ?? row.horas_declaradas ?? 0}h
      </span>
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
    label: 'Data Submissão',
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

export default function FilaRevisao() {
  const [certificados, setCertificados] = useState([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState(null)
  const [certificadoSelecionado, setCertificado] = useState(null)

  const fetchFila = useCallback(async () => {
    try {
      setLoading(true)
      setErro(null)
      const { data } = await certificadosService.listar()
      const allCerts = Array.isArray(data) ? data : (data.results ?? [])
      
      // Filtrar apenas pendentes ou em revisão
      const fila = allCerts.filter(c => ['pendente_ocr', 'revisao_manual'].includes(c.status))
      
      // Ordenar por data (mais antigos primeiro para FIFO)
      fila.sort((a, b) => new Date(a.data_envio) - new Date(b.data_envio))
      
      setCertificados(fila)
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar fila de revisão.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchFila() }, [fetchFila])

  return (
    <AppLayout
      breadcrumb={
        <div className="min-w-0 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-warning" />
          <p className="text-label font-medium text-text-primary truncate">Fila de Revisão</p>
        </div>
      }
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h1 className="text-h3 font-bold text-text-primary">Fila de Revisão</h1>
          <p className="text-label text-text-secondary mt-1">
            {certificados.length} certificado(s) aguardando análise manual.
          </p>
        </div>

        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-3 h-9 rounded-xs border border-border bg-bg-surface hover:bg-bg transition-colors text-label font-medium">
            <Filter className="h-4 w-4" />
            Filtrar
          </button>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
            <input
              type="text"
              placeholder="Buscar matrícula..."
              className="pl-9 pr-3 h-9 rounded-xs border border-border bg-bg-surface text-label focus:ring-2 focus:ring-primary outline-none"
            />
          </div>
        </div>
      </div>

      {erro ? (
        <div className="surface rounded-sm p-6 flex items-center gap-3 text-danger mb-4">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="text-label font-semibold">Erro ao carregar dados</p>
            <p className="text-helper mt-0.5">{erro}</p>
          </div>
        </div>
      ) : (
        <DataTable
          columns={COLUMNS}
          data={certificados}
          loading={loading}
          emptyLabel="Fila vazia! Nenhum certificado aguardando revisão."
          onRowClick={(row) => setCertificado(row)}
        />
      )}

      <CertificadoDrawer
        certificado={certificadoSelecionado}
        onClose={() => setCertificado(null)}
        onAvaliado={fetchFila}
      />
    </AppLayout>
  )
}
