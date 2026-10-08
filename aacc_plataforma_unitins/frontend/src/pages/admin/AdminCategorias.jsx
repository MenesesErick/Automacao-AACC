import { useState, useEffect, useCallback } from 'react'
import { Plus, Edit2, Trash2, X, AlertCircle } from 'lucide-react'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { DataTable } from '@/components/organisms/DataTable'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { eixosService, categoriasService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

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

export default function AdminCategorias() {
  const [activeTab, setActiveTab] = useState('eixos')
  const [eixos, setEixos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Modais de Eixo
  const [isEixoModalOpen, setIsEixoModalOpen] = useState(false)
  const [eixoForm, setEixoForm] = useState({ id: null, nome: '' })

  // Modais de Categoria
  const [isCatModalOpen, setIsCatModalOpen] = useState(false)
  const [catForm, setCatForm] = useState({ id: null, nome: '', teto_horas: '', eixo: '' })

  const fetchDados = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (activeTab === 'eixos') {
        const { data } = await eixosService.listar()
        setEixos(Array.isArray(data) ? data : data.results || [])
      } else {
        const { data } = await categoriasService.listar()
        setCategorias(Array.isArray(data) ? data : data.results || [])
        // Preenche eixos caso o usuário vá abrir o form de criar categoria
        if (eixos.length === 0) {
          const res = await eixosService.listar()
          setEixos(Array.isArray(res.data) ? res.data : res.data.results || [])
        }
      }
    } catch (err) {
      setError(err.friendlyMessage || 'Erro ao buscar dados.')
    } finally {
      setLoading(false)
    }
  }, [activeTab, eixos.length])

  useEffect(() => {
    fetchDados()
  }, [fetchDados])

  // ===================== CRUD EIXOS =====================
  const handleOpenEixoModal = (eixo = null) => {
    setEixoForm(eixo ? { id: eixo.id, nome: eixo.nome } : { id: null, nome: '' })
    setIsEixoModalOpen(true)
  }

  const handleSaveEixo = async (e) => {
    e.preventDefault()
    try {
      if (eixoForm.id) {
        await eixosService.atualizar(eixoForm.id, { nome: eixoForm.nome })
      } else {
        await eixosService.criar({ nome: eixoForm.nome })
      }
      setIsEixoModalOpen(false)
      fetchDados()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao salvar eixo')
    }
  }

  const handleDeleteEixo = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este eixo?')) return
    try {
      await eixosService.remover(id)
      fetchDados()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao excluir eixo')
    }
  }

  // ===================== CRUD CATEGORIAS =====================
  const handleOpenCatModal = (cat = null) => {
    setCatForm(cat ? { id: cat.id, nome: cat.nome, teto_horas: cat.teto_horas, eixo: cat.eixo } : { id: null, nome: '', teto_horas: '', eixo: '' })
    setIsCatModalOpen(true)
  }

  const handleSaveCat = async (e) => {
    e.preventDefault()
    try {
      const payload = { 
        nome: catForm.nome, 
        teto_horas: parseInt(catForm.teto_horas, 10), 
        eixo: parseInt(catForm.eixo, 10) 
      }
      if (catForm.id) {
        await categoriasService.atualizar(catForm.id, payload)
      } else {
        await categoriasService.criar(payload)
      }
      setIsCatModalOpen(false)
      fetchDados()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao salvar categoria')
    }
  }

  const handleDeleteCat = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta categoria?')) return
    try {
      await categoriasService.remover(id)
      fetchDados()
    } catch (err) {
      alert(err.friendlyMessage || 'Erro ao excluir categoria')
    }
  }

  // ===================== COLUNAS =====================
  const eixoColumns = [
    { key: 'id', label: 'ID', render: (row) => <span className="font-mono text-gray-500">#{row.id}</span> },
    { key: 'nome', label: 'Nome' },
    {
      key: 'actions', label: '', render: (row) => (
        <div className="flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="xs" onClick={() => handleOpenEixoModal(row)}><Edit2 className="w-4 h-4 text-blue-600" /></Button>
          <Button variant="ghost" size="xs" onClick={() => handleDeleteEixo(row.id)}><Trash2 className="w-4 h-4 text-red-600" /></Button>
        </div>
      )
    }
  ]

  const catColumns = [
    { key: 'id', label: 'ID', render: (row) => <span className="font-mono text-gray-500">#{row.id}</span> },
    { key: 'eixo_nome', label: 'Eixo', render: (row) => <span className="text-gray-600 font-medium">{eixos.find(e => e.id === row.eixo)?.nome || `Eixo #${row.eixo}`}</span> },
    { key: 'nome', label: 'Nome' },
    { key: 'teto_horas', label: 'Teto (h)', render: (row) => <span className="font-mono">{row.teto_horas}h</span> },
    {
      key: 'actions', label: '', render: (row) => (
        <div className="flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="xs" onClick={() => handleOpenCatModal(row)}><Edit2 className="w-4 h-4 text-blue-600" /></Button>
          <Button variant="ghost" size="xs" onClick={() => handleDeleteCat(row.id)}><Trash2 className="w-4 h-4 text-red-600" /></Button>
        </div>
      )
    }
  ]

  return (
    <AdminLayout title="Eixos e Categorias">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header com Abas */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex bg-gray-200/50 p-1 rounded-lg w-fit">
            <button
              onClick={() => setActiveTab('eixos')}
              className={cn('px-4 py-2 text-sm font-medium rounded-md transition-all', activeTab === 'eixos' ? 'bg-white text-slate-900 shadow-sm' : 'text-gray-500 hover:text-gray-700')}
            >
              Eixos Formativos
            </button>
            <button
              onClick={() => setActiveTab('categorias')}
              className={cn('px-4 py-2 text-sm font-medium rounded-md transition-all', activeTab === 'categorias' ? 'bg-white text-slate-900 shadow-sm' : 'text-gray-500 hover:text-gray-700')}
            >
              Categorias
            </button>
          </div>
          
          <Button 
            onClick={() => activeTab === 'eixos' ? handleOpenEixoModal() : handleOpenCatModal()}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            {activeTab === 'eixos' ? 'Novo Eixo' : 'Nova Categoria'}
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-md flex gap-3 items-center">
            <AlertCircle className="w-5 h-5" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-xs border border-gray-100 p-1">
          {activeTab === 'eixos' ? (
            <DataTable columns={eixoColumns} data={eixos} loading={loading} emptyLabel="Nenhum Eixo Formativo cadastrado." />
          ) : (
            <DataTable columns={catColumns} data={categorias} loading={loading} emptyLabel="Nenhuma Categoria cadastrada." />
          )}
        </div>
      </div>

      {/* Modais */}
      <Modal isOpen={isEixoModalOpen} onClose={() => setIsEixoModalOpen(false)} title={eixoForm.id ? "Editar Eixo" : "Criar Eixo"}>
        <form onSubmit={handleSaveEixo} className="space-y-4">
          <Input 
            label="Nome do Eixo" 
            placeholder="Ex: Ensino" 
            value={eixoForm.nome} 
            onChange={e => setEixoForm({...eixoForm, nome: e.target.value})} 
            required 
            autoFocus 
          />
          <div className="pt-4 flex justify-end gap-3">
            <Button variant="ghost" type="button" onClick={() => setIsEixoModalOpen(false)}>Cancelar</Button>
            <Button type="submit">Salvar</Button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={isCatModalOpen} onClose={() => setIsCatModalOpen(false)} title={catForm.id ? "Editar Categoria" : "Criar Categoria"}>
        <form onSubmit={handleSaveCat} className="space-y-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Eixo Formativo</label>
            <select 
              className="h-10 px-3 w-full rounded-md border border-gray-300 bg-white text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              value={catForm.eixo}
              onChange={e => setCatForm({...catForm, eixo: e.target.value})}
              required
            >
              <option value="" disabled>Selecione um eixo...</option>
              {eixos.map(eixo => (
                <option key={eixo.id} value={eixo.id}>{eixo.nome}</option>
              ))}
            </select>
          </div>
          <Input 
            label="Nome da Categoria" 
            placeholder="Ex: Monitoria" 
            value={catForm.nome} 
            onChange={e => setCatForm({...catForm, nome: e.target.value})} 
            required 
          />
          <Input 
            label="Teto de Horas" 
            type="number"
            min="1"
            placeholder="Ex: 60" 
            value={catForm.teto_horas} 
            onChange={e => setCatForm({...catForm, teto_horas: e.target.value})} 
            required 
          />
          <div className="pt-4 flex justify-end gap-3">
            <Button variant="ghost" type="button" onClick={() => setIsCatModalOpen(false)}>Cancelar</Button>
            <Button type="submit">Salvar</Button>
          </div>
        </form>
      </Modal>

    </AdminLayout>
  )
}
