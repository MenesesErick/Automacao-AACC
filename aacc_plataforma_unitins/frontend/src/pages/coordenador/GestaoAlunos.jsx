import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Users, AlertCircle, BookOpen, ArrowRight } from 'lucide-react'
import { AppLayout } from '@/components/layout/AppLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { alunoService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

const COLUMNS = [
  {
    key: 'matricula',
    label: 'Matrícula',
    render: (r) => (
      <span className="text-label font-semibold text-text-primary font-mono">{r.matricula}</span>
    ),
  },
  {
    key: 'aluno_nome',
    label: 'Nome',
    render: (r) => (
      <p className="text-label font-medium text-text-primary truncate max-w-[180px]">{r.aluno_nome}</p>
    ),
  },
  {
    key: 'email',
    label: 'E-mail',
    render: (r) => (
      <span className="text-label text-text-secondary truncate max-w-[180px] block">{r.email}</span>
    ),
  },
  {
    key: 'curso',
    label: 'Curso',
    render: (r) => (
      <div className="flex items-center gap-1.5">
        <BookOpen className="h-3.5 w-3.5 text-text-secondary shrink-0" />
        <span className="text-label text-text-secondary truncate max-w-[140px]">{r.curso}</span>
      </div>
    ),
  },
  {
    key: 'horas_aprovadas',
    label: 'Horas Aprovadas',
    render: (r) => (
      <span className={cn(
        'text-label font-bold tabular-nums',
        r.horas_aprovadas > 0 ? 'text-success' : 'text-text-disabled',
      )}>
        {r.horas_aprovadas}h
      </span>
    ),
  },
  {
    key: 'total_certs',
    label: 'Certificados',
    render: (r) => (
      <span className="text-label text-text-primary">{r.total_certs}</span>
    ),
  },
  {
    key: 'action',
    label: '',
    render: () => (
      <div className="flex items-center gap-1 text-primary opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="text-helper font-medium">Ver Dossiê</span>
        <ArrowRight className="h-3.5 w-3.5" />
      </div>
    ),
  },
]

export default function GestaoAlunos() {
  const navigate = useNavigate()
  const [alunos,  setAlunos]  = useState([])
  const [busca,   setBusca]   = useState('')
  const [loading, setLoading] = useState(true)
  const [erro,    setErro]    = useState(null)

  const fetchAlunos = useCallback(async () => {
    try {
      setLoading(true)
      setErro(null)
      const { data } = await alunoService.listarAlunos()
      setAlunos(Array.isArray(data) ? data : [])
    } catch (err) {
      setErro(err.friendlyMessage ?? 'Erro ao carregar lista de alunos.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchAlunos() }, [fetchAlunos])

  const alunosFiltrados = alunos.filter((a) => {
    const q = busca.toLowerCase().trim()
    if (!q) return true
    return (
      a.aluno_nome?.toLowerCase().includes(q) ||
      a.matricula?.toLowerCase().includes(q) ||
      a.email?.toLowerCase().includes(q)
    )
  })

  return (
    <AppLayout
      breadcrumb={
        <div className="min-w-0 flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" />
          <p className="text-label font-medium text-text-primary truncate">Gestão de Alunos</p>
        </div>
      }
    >
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h1 className="text-h3 font-bold text-text-primary">Gestão de Alunos</h1>
          <p className="text-label text-text-secondary mt-1">
            {loading ? '...' : `${alunos.length} aluno(s) cadastrado(s).`}
            {' '}Clique num aluno para abrir o Dossiê completo.
          </p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary pointer-events-none" />
          <input
            type="text"
            placeholder="Buscar por nome, matrícula ou e-mail..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="pl-9 pr-4 h-9 w-72 rounded-xs border border-border bg-bg-surface text-label focus:ring-2 focus:ring-primary outline-none transition-shadow"
          />
        </div>
      </div>

      {/* Tabela */}
      {erro ? (
        <div className="surface rounded-sm p-6 flex items-center gap-3 text-danger">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <div>
            <p className="text-label font-semibold">Erro ao carregar dados</p>
            <p className="text-helper mt-0.5">{erro}</p>
          </div>
        </div>
      ) : (
        <DataTable
          columns={COLUMNS}
          data={alunosFiltrados}
          loading={loading}
          emptyLabel={busca
            ? `Nenhum aluno encontrado para "${busca}".`
            : 'Nenhum aluno cadastrado no sistema.'}
          onRowClick={(row) => navigate(`/coordenador/alunos/${row.id}`)}
        />
      )}
    </AppLayout>
  )
}
