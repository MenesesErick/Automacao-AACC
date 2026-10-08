import { useState, useEffect, useCallback } from 'react'
import { Plus, Edit2, Trash2, X, AlertCircle } from 'lucide-react'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { cursosService } from '@/services/api/endpoints'

function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  )
}

export default function AdminCursos() {
  const [cursos, setCursos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form, setForm] = useState({ id: null, nome: '', codigo: '', horas_totais_exigidas: '', ano_vigencia: '' })

  const fetchCursos = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await cursosService.listar()
      setCursos(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.friendlyMessage || 'Erro ao buscar cursos.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCursos()
  }, [fetchCursos])

  const handleOpenModal = (curso = null) => {
    setForm(curso 
      ? { 
          id: curso.id, 
          nome: curso.nome, 
          codigo: curso.codigo || '', 
          horas_totais_exigidas: curso.horas_totais_exigidas || 180, 
          ano_vigencia: curso.ano_vigencia || new Date().getFullYear() 
        } 
      : { id: null, nome: '', codigo: '', horas_totais_exigidas: 180, ano_vigencia: new Date().getFullYear() }
    )
    setIsModalOpen(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      const payload = { 
        nome: form.nome, 
        codigo: form.codigo, 
        horas_totais_exigidas: parseInt(form.horas_totais_exigidas, 10), 
        ano_vigencia: parseInt(form.ano_vigencia, 10) 
      }
      
      if (form.id) {
        await cursosService.atualizar(form.id, payload)
      } else {
        await cursosService.criar(payload)
      }
      setIsModalOpen(false)
      fetchCursos()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao salvar curso')
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este curso? (Pode falhar se houver alunos vinculados)')) return
    try {
      await cursosService.remover(id)
      fetchCursos()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao excluir curso')
    }
  }

  const columns = [
    { key: 'id', label: 'ID', render: (row) => <span className="font-mono text-gray-500">#{row.id}</span> },
    { key: 'nome', label: 'Nome do Curso', render: (row) => <span className="font-medium text-gray-800">{row.nome}</span> },
    { key: 'codigo', label: 'Código', render: (row) => <span className="text-gray-500">{row.codigo || '—'}</span> },
    { key: 'horas', label: 'Meta (h)', render: (row) => <span className="font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs">{row.horas_totais_exigidas}h</span> },
    { key: 'ano_vigencia', label: 'Vigência', render: (row) => <span className="text-gray-500">{row.ano_vigencia || '—'}</span> },
    {
      key: 'actions', label: '', render: (row) => (
        <div className="flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="xs" onClick={() => handleOpenModal(row)}><Edit2 className="w-4 h-4 text-blue-600" /></Button>
          <Button variant="ghost" size="xs" onClick={() => handleDelete(row.id)}><Trash2 className="w-4 h-4 text-red-600" /></Button>
        </div>
      )
    }
  ]

  return (
    <AdminLayout title="Cursos e Matrizes">
      <div className="max-w-5xl mx-auto space-y-6">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Gestão de Cursos</h2>
            <p className="text-sm text-gray-500">Cadastre cursos e defina as metas horárias das matrizes curriculares.</p>
          </div>
          <Button onClick={() => handleOpenModal()} leftIcon={<Plus className="w-4 h-4" />}>
            Novo Curso
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-md flex gap-3 items-center">
            <AlertCircle className="w-5 h-5" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-xs border border-gray-100 p-1">
          <DataTable columns={columns} data={cursos} loading={loading} emptyLabel="Nenhum curso cadastrado." />
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={form.id ? "Editar Curso" : "Criar Curso"}>
        <form onSubmit={handleSave} className="space-y-4">
          <Input 
            label="Nome do Curso" 
            placeholder="Ex: Sistemas de Informação" 
            value={form.nome} 
            onChange={e => setForm({...form, nome: e.target.value})} 
            required 
            autoFocus 
          />
          <Input 
            label="Código (Opcional)" 
            placeholder="Ex: SI01" 
            value={form.codigo} 
            onChange={e => setForm({...form, codigo: e.target.value})} 
          />
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Horas Exigidas (Meta)</label>
              <select 
                className="h-10 px-3 w-full rounded-md border border-gray-300 bg-white text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                value={form.horas_totais_exigidas}
                onChange={e => setForm({...form, horas_totais_exigidas: e.target.value})}
                required
              >
                <option value="120">120 horas</option>
                <option value="180">180 horas</option>
                <option value="200">200 horas</option>
                <option value="240">240 horas</option>
              </select>
            </div>
            <Input 
              label="Ano de Vigência" 
              type="number"
              min="2000"
              placeholder="Ex: 2025" 
              value={form.ano_vigencia} 
              onChange={e => setForm({...form, ano_vigencia: e.target.value})} 
              required 
            />
          </div>
          <div className="pt-4 flex justify-end gap-3">
            <Button variant="ghost" type="button" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
            <Button type="submit">Salvar</Button>
          </div>
        </form>
      </Modal>
    </AdminLayout>
  )
}
