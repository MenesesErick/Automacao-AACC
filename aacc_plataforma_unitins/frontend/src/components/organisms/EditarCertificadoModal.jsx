/**
 * EditarCertificadoModal.jsx — UC01.5 (Retificar submissão)
 *
 * Reaproveita os campos de SubmeterCertificado (Categoria, Arquivo, Título, Período),
 * pré-preenchidos com os dados atuais. Envia PATCH via certificadosService.atualizar().
 */
import { useEffect, useState } from 'react'
import { Loader2, AlertTriangle, X, Layers, Type, Calendar, Upload, Info, Pencil } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/utils/cn'
import { categoriasService, certificadosService } from '@/services/api/endpoints'
import { DropZone, agruparPorEixo } from '@/pages/aluno/SubmeterCertificado'

const inputCls = (erro) => cn(
  'w-full h-10 rounded-xs border px-3 text-label bg-bg focus:ring-2 focus:ring-primary outline-none transition-shadow',
  erro ? 'border-danger' : 'border-border',
)

export function EditarCertificadoModal({ cert, onClose, onSaved }) {
  const [categorias, setCategorias] = useState([])
  const [categoriaId, setCategoriaId] = useState(String(cert.categoria ?? ''))
  const [titulo, setTitulo] = useState(cert.titulo_atividade ?? '')
  const [periodo, setPeriodo] = useState(cert.periodo_realizacao ?? '')
  const [arquivo, setArquivo] = useState(null)
  const [erros, setErros] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    categoriasService.listar()
      .then(({ data }) => setCategorias(Array.isArray(data) ? data : (data.results ?? [])))
      .catch(() => toast.error('Não foi possível carregar as categorias.'))
  }, [])

  const nomeArquivoAtual = cert.arquivo_pdf ? decodeURIComponent(cert.arquivo_pdf.split('/').pop()) : null
  const grupos = agruparPorEixo(categorias)
  const catSelecionada = categorias.find(c => String(c.id) === String(categoriaId))

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    const e = {}
    if (!categoriaId) e.categoria = 'Selecione a categoria.'
    if (!titulo.trim()) e.titulo = 'Informe o título da atividade.'
    if (!periodo.trim()) e.periodo = 'Informe o período de realização.'
    setErros(e)
    if (Object.keys(e).length) return

    const fd = new FormData()
    fd.append('categoria', categoriaId)
    fd.append('titulo_atividade', titulo.trim())
    fd.append('periodo_realizacao', periodo.trim())
    if (arquivo) fd.append('arquivo_pdf', arquivo)

    try {
      setSaving(true)
      await certificadosService.atualizar(cert.id, fd)
      toast.success('Submissão retificada com sucesso!')
      onSaved?.()
    } catch (err) {
      const d = err.response?.data
      toast.error('Falha ao salvar', {
        description: d?.detail || d?.arquivo_pdf?.[0] || d?.categoria?.[0] || err.friendlyMessage || 'Erro ao atualizar o certificado.',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" role="dialog" aria-modal="true">
      <form
        onSubmit={handleSubmit}
        className="surface bg-bg-surface rounded-sm border border-border w-full max-w-xl max-h-[90vh] overflow-y-auto shadow-xl"
      >
        <div className="px-6 py-4 border-b border-border bg-bg flex items-center gap-3 sticky top-0 z-10">
          <div className="h-9 w-9 rounded-sm bg-primary/10 flex items-center justify-center shrink-0">
            <Pencil className="h-4 w-4 text-primary" />
          </div>
          <div className="flex-1">
            <h2 className="text-label font-bold text-text-primary">Retificar Certificado</h2>
            <p className="text-helper text-text-secondary">Edite os dados ou troque o arquivo enquanto estiver em análise.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar" className="text-text-secondary hover:text-text-primary">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Categoria */}
          <div>
            <label htmlFor="edit-categoria" className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-text-secondary" /> Categoria da Atividade <span className="text-danger">*</span>
            </label>
            <select
              id="edit-categoria"
              value={categoriaId}
              onChange={(e) => { setCategoriaId(e.target.value); setErros(p => ({ ...p, categoria: '' })) }}
              className={inputCls(erros.categoria)}
            >
              <option value="" disabled>Selecione a categoria...</option>
              {Object.entries(grupos).map(([eixo, cats]) => (
                <optgroup key={eixo} label={`── ${eixo}`}>
                  {cats.map(cat => <option key={cat.id} value={cat.id}>{cat.nome}</option>)}
                </optgroup>
              ))}
            </select>
            {erros.categoria && <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5"><AlertTriangle className="h-3.5 w-3.5" /> {erros.categoria}</p>}
            {catSelecionada?.tooltip_display && (
              <div className="mt-3 flex gap-2.5 rounded-sm border border-primary-muted bg-primary-light/80 p-3 text-primary-hover">
                <Info className="h-4 w-4 shrink-0 mt-0.5 text-primary" />
                <p className="text-helper font-medium leading-relaxed">{catSelecionada.tooltip_display}</p>
              </div>
            )}
          </div>

          {/* Arquivo */}
          <div>
            <label className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5">
              <Upload className="h-4 w-4 text-text-secondary" /> Ficheiro do Certificado
            </label>
            {!arquivo && nomeArquivoAtual && (
              <p className="text-helper text-text-secondary mb-2">
                Arquivo atual: <span className="font-semibold text-text-primary">{nomeArquivoAtual}</span>
              </p>
            )}
            <DropZone arquivo={arquivo} onChange={setArquivo} erro={erros.arquivo} analisando={false} />
            <p className="text-helper text-text-secondary mt-1.5">Opcional — selecione apenas se quiser substituir o arquivo atual.</p>
          </div>

          {/* Título */}
          <div>
            <label htmlFor="edit-titulo" className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5">
              <Type className="h-4 w-4 text-text-secondary" /> Título da Atividade <span className="text-danger">*</span>
            </label>
            <input
              id="edit-titulo" type="text" value={titulo}
              onChange={(e) => { setTitulo(e.target.value); setErros(p => ({ ...p, titulo: '' })) }}
              className={inputCls(erros.titulo)}
            />
            {erros.titulo && <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5"><AlertTriangle className="h-3.5 w-3.5" /> {erros.titulo}</p>}
          </div>

          {/* Período */}
          <div>
            <label htmlFor="edit-periodo" className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-text-secondary" /> Período de Realização <span className="text-danger">*</span>
            </label>
            <input
              id="edit-periodo" type="text" value={periodo}
              onChange={(e) => { setPeriodo(e.target.value); setErros(p => ({ ...p, periodo: '' })) }}
              className={inputCls(erros.periodo)}
            />
            {erros.periodo && <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5"><AlertTriangle className="h-3.5 w-3.5" /> {erros.periodo}</p>}
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 h-10 rounded-xs border border-border text-label font-medium text-text-secondary hover:bg-bg transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving}
              className={cn(
                'flex-1 h-10 rounded-xs text-white font-semibold text-label flex items-center justify-center gap-2 transition-colors',
                saving ? 'bg-primary/60 cursor-not-allowed' : 'bg-primary hover:bg-primary-hover',
              )}>
              {saving ? <><Loader2 className="h-4 w-4 animate-spin" /> Salvando...</> : 'Salvar alterações'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
