import { useState, useEffect, useCallback } from 'react'
import { Plus, X, AlertCircle } from 'lucide-react'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { coordenadoresService, cursosService } from '@/services/api/endpoints'

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

export default function AdminCoordenadores() {
  const [coordenadores, setCoordenadores] = useState([])
  const [cursos, setCursos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form, setForm] = useState({ first_name: '', email: '', cpf: '', password: '', curso_id: '' })

  const fetchDados = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resCoord = await coordenadoresService.listar()
      setCoordenadores(Array.isArray(resCoord.data) ? resCoord.data : resCoord.data.results || [])
      
      const resCursos = await cursosService.listar()
      setCursos(Array.isArray(resCursos.data) ? resCursos.data : resCursos.data.results || [])
    } catch (err) {
      setError(err.friendlyMessage || 'Erro ao buscar dados.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDados()
  }, [fetchDados])

  const handleOpenModal = () => {
    setForm({ first_name: '', email: '', cpf: '', password: '', curso_id: '' })
    setIsModalOpen(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    
    if (!form.email.toLowerCase().endsWith('@unitins.br')) {
      alert('O email deve pertencer ao domínio @unitins.br')
      return
    }

    try {
      await coordenadoresService.criar({
        first_name: form.first_name,
        email: form.email,
        cpf: form.cpf,
        password: form.password,
        curso_id: form.curso_id,
      })
      setIsModalOpen(false)
      fetchDados()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao cadastrar coordenador')
    }
  }

  const columns = [
    { key: 'first_name', label: 'Nome', render: (row) => <span className="font-medium text-gray-800">{row.first_name || '—'}</span> },
    { key: 'email', label: 'E-mail', render: (row) => <span className="text-gray-600">{row.email}</span> },
    { key: 'cpf', label: 'CPF', render: (row) => <span className="text-gray-500 font-mono text-xs">{row.cpf}</span> },
    { key: 'curso_nome', label: 'Curso Vinculado', render: (row) => <span className="bg-green-50 text-green-700 px-2 py-0.5 rounded text-xs">{row.curso_nome || 'Não Vinculado'}</span> },
  ]

  return (
    <AdminLayout title="Coordenadores">
      <div className="max-w-5xl mx-auto space-y-6">
        
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Gestão de Coordenadores</h2>
            <p className="text-sm text-gray-500">Crie contas e vincule aos cursos (Isolamento de Visão de Dados).</p>
          </div>
          <Button onClick={handleOpenModal} leftIcon={<Plus className="w-4 h-4" />}>
            Novo Coordenador
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-md flex gap-3 items-center">
            <AlertCircle className="w-5 h-5" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-xs border border-gray-100 p-1">
          <DataTable columns={columns} data={coordenadores} loading={loading} emptyLabel="Nenhum coordenador cadastrado." />
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Criar Coordenador">
        <form onSubmit={handleSave} className="space-y-4">
          <Input 
            label="Nome Completo" 
            placeholder="Ex: Maria José" 
            value={form.first_name} 
            onChange={e => setForm({...form, first_name: e.target.value})} 
            required 
            autoFocus 
          />
          <Input 
            label="E-mail Institucional" 
            type="email"
            placeholder="maria@unitins.br" 
            value={form.email} 
            onChange={e => setForm({...form, email: e.target.value})} 
            required 
          />
          <div className="grid grid-cols-2 gap-4">
            <Input 
              label="CPF" 
              placeholder="000.000.000-00" 
              value={form.cpf} 
              onChange={e => setForm({...form, cpf: e.target.value})} 
              required 
            />
            <Input 
              label="Senha Inicial" 
              type="password"
              placeholder="Min 8 caracteres" 
              value={form.password} 
              onChange={e => setForm({...form, password: e.target.value})} 
              required 
            />
          </div>
          
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Curso Vinculado</label>
            <select 
              className="h-10 px-3 w-full rounded-md border border-gray-300 bg-white text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              value={form.curso_id}
              onChange={e => setForm({...form, curso_id: e.target.value})}
              required
            >
              <option value="" disabled>Selecione um curso para blindagem de dados...</option>
              {cursos.map(c => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3">
            <Button variant="ghost" type="button" onClick={() => setIsModalOpen(false)}>Cancelar</Button>
            <Button type="submit">Cadastrar</Button>
          </div>
        </form>
      </Modal>
    </AdminLayout>
  )
}
