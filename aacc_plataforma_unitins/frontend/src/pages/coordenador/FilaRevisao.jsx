import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShieldCheck, AlertCircle, Search, Filter, ChevronRight, ArrowRight
} from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { Badge } from '@/components/atoms/Badge'
import { certificadosService } from '@/services/api/endpoints'

const STATUS_MAP = {
  pendente_ocr: { label: 'Pendente OCR', variant: 'default' },
  revisao_manual: { label: 'Revisão Manual', variant: 'warning' },
}

export default function FilaRevisao() {
  const navigate = useNavigate()
  const [certificados, setCertificados] = useState([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState(null)
  const [busca, setBusca] = useState('')
  const [filtroStatus, setFiltroStatus] = useState('todas') // 'todas' | 'pendente_ocr' | 'revisao_manual'
  const [filtroCurso, setFiltroCurso] = useState('')

  const fetchFila = useCallback(async () => {
    try {
      setLoading(true)
      setErro(null)
      const { data } = await certificadosService.listar()
      const allCerts = Array.isArray(data) ? data : (data.results ?? [])

      // Filtrar apenas pendentes ou em revisão
      const fila = allCerts.filter(c => ['pendente_ocr', 'revisao_manual'].includes(c.status))

      // Ordenar por data (mais antigos primeiro — FIFO)
      fila.sort((a, b) => new Date(a.data_envio) - new Date(b.data_envio))

      setCertificados(fila)
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar fila de revisão.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchFila() }, [fetchFila])

  const handleRowClick = (row) => {
    navigate(`/coordenador/certificados/${row.id}`)
  }

  const filtrados = certificados.filter(c =>
    !busca || String(c.aluno).includes(busca) || (c.categoria_nome ?? '').toLowerCase().includes(busca.toLowerCase())
  )

  const COLUMNS = [
    {
      key: 'id',
      label: '#',
      render: (row) => (
        <span className="text-helper text-text-disabled font-mono">#{row.id}</span>
      ),
    },
    {
      key: 'matricula',
      label: 'Matricula',
      render: (row) => (
        <div className="min-w-0">
          <p className="text-label font-medium text-text-primary truncate max-w-[150px]">
            Matrícula {row.aluno}
          </p>
        </div>
      ),
    },
    {
      key: 'aluno',
      label: 'Aluno',
      render: (row) => (
        <div className="min-w-0">
          <p className="text-label font-medium text-text-primary truncate max-w-[150px]">
            {row.aluno_nome}
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
        <div className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-helper font-medium">Avaliar</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </div>
      ),
    },
  ]

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
            {loading
              ? 'Carregando...'
              : `${filtrados.length} certificado(s) aguardando análise manual.`}
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
              value={busca}
              onChange={e => setBusca(e.target.value)}
              placeholder="Buscar matrícula, Nome ou categoria..."
              className="pl-9 pr-3 h-9 rounded-xs border border-border bg-bg-surface text-label focus:ring-2 focus:ring-primary outline-none w-64"
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
          data={filtrados}
          loading={loading}
          emptyLabel="Fila vazia! Nenhum certificado aguardando revisão."
          onRowClick={handleRowClick}
        />
      )}
    </AppLayout>
  )
}
