/**
 * SubmeterCertificado.jsx — Envio de Certificado AACC pelo Aluno
 *
 * Formulário de submissão com Copiloto Inteligente:
 *   - Seleção de categoria (categoriasService.listar())
 *   - Upload com drag-and-drop → dispara analise-previa/ automaticamente
 *   - Campos de Título e Período pré-preenchidos pela IA (editáveis)
 *   - Submit via FormData → certificadosService.criar()
 *   - Feedback com sonner toast + redirecionamento
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Upload, FileText, CheckCircle2,
  Loader2, AlertTriangle, FolderOpen, Layers, X, Info,
  Sparkles, Calendar, Type,
} from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/utils/cn'
import { categoriasService, certificadosService } from '@/services/api/endpoints'

// ─── Agrupamento de categorias por eixo ──────────────────────────────────────
function agruparPorEixo(categorias) {
  return categorias.reduce((acc, cat) => {
    const eixo = cat.eixo_nome || 'Outros'
    if (!acc[eixo]) acc[eixo] = []
    acc[eixo].push(cat)
    return acc
  }, {})
}

// ─── Drop Zone com preview ────────────────────────────────────────────────────
function DropZone({ arquivo, onChange, erro, analisando }) {
  const [drag, setDrag] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDrag(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onChange(file)
  }

  const formatBytes = (bytes) => {
    if (bytes < 1024)        return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div>
      <label
        htmlFor="arquivo-input"
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        className={cn(
          'flex flex-col items-center justify-center gap-3 rounded-sm border-2 border-dashed p-10 cursor-pointer transition-all',
          drag
            ? 'border-primary bg-primary/5'
            : arquivo
              ? 'border-success bg-success-light/40'
              : erro
                ? 'border-danger bg-danger-light/30'
                : 'border-border bg-bg hover:border-primary/60 hover:bg-primary/5',
        )}
      >
        {analisando ? (
          <>
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Loader2 className="h-6 w-6 text-primary animate-spin" />
            </div>
            <div className="text-center">
              <p className="text-label font-semibold text-primary">Copiloto analisando...</p>
              <p className="text-helper text-text-secondary mt-0.5">Extraindo metadados do documento</p>
            </div>
          </>
        ) : arquivo ? (
          <>
            <div className="h-12 w-12 rounded-full bg-success/20 flex items-center justify-center">
              <FileText className="h-6 w-6 text-success" />
            </div>
            <div className="text-center">
              <p className="text-label font-semibold text-success truncate max-w-xs">{arquivo.name}</p>
              <p className="text-helper text-text-secondary mt-0.5">{formatBytes(arquivo.size)}</p>
            </div>
            <p className="text-helper text-text-secondary">Clique para trocar o ficheiro</p>
          </>
        ) : (
          <>
            <div className={cn(
              'h-12 w-12 rounded-full flex items-center justify-center transition-colors',
              drag ? 'bg-primary/20' : 'bg-bg-surface',
            )}>
              <Upload className={cn('h-6 w-6', drag ? 'text-primary' : 'text-text-disabled')} />
            </div>
            <div className="text-center">
              <p className="text-label font-semibold text-text-primary">
                {drag ? 'Solte o ficheiro aqui' : 'Arraste ou clique para selecionar'}
              </p>
              <p className="text-helper text-text-secondary mt-0.5">PDF, PNG ou JPG — máx. 10 MB</p>
            </div>
          </>
        )}
      </label>

      <input
        id="arquivo-input"
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="sr-only"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onChange(f) }}
      />

      {erro && (
        <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          {erro}
        </p>
      )}
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function SubmeterCertificado() {
  const navigate = useNavigate()

  const [categorias,  setCategorias]  = useState([])
  const [loadingCats, setLoadingCats] = useState(true)
  const [erroCats,    setErroCats]    = useState(null)

  const [categoriaId,      setCategoriaId]      = useState('')
  const [arquivo,          setArquivo]          = useState(null)
  const [titulo,           setTitulo]           = useState('')
  const [periodo,          setPeriodo]          = useState('')
  const [analisando,       setAnalisando]       = useState(false)
  const [coPilotoUsado,    setCoPilotoUsado]    = useState(false)
  const [leituraImagem,    setLeituraImagem]    = useState(false)
  const [submitting,       setSubmitting]       = useState(false)
  const [sucesso,          setSucesso]          = useState(false)
  const [erros,            setErros]            = useState({
    categoria: '', arquivo: '', titulo: '', periodo: '',
  })

  // Busca categorias ao montar
  useEffect(() => {
    categoriasService.listar()
      .then(({ data }) => {
        const lista = Array.isArray(data) ? data : (data.results ?? [])
        setCategorias(lista)
      })
      .catch(() => setErroCats('Não foi possível carregar as categorias.'))
      .finally(() => setLoadingCats(false))
  }, [])

  // ── Copiloto: chama analise-previa/ ao selecionar arquivo ────────────────
  const handleArquivo = async (file) => {
    setArquivo(file)
    setErros(prev => ({ ...prev, arquivo: '' }))
    setAnalisando(true)
    setCoPilotoUsado(false)
    setLeituraImagem(false)

    try {
      const { data } = await certificadosService.analisarPrevia(file)
      console.log("Resposta da API:", data)
      
      if (data.titulo_sugerido || data.periodo_sugerido) {
        setTitulo(data.titulo_sugerido || '')
        setPeriodo(data.periodo_sugerido || '')
        setCoPilotoUsado(true)
        setLeituraImagem(data.leitura_por_imagem === true)
      } else {
        toast.info("A IA não conseguiu ler os dados automaticamente. Preencha manualmente.")
      }
    } catch {
      toast.error("Falha ao comunicar com o assistente de extração.")
    } finally {
      setAnalisando(false)
    }
  }

  // ── Validação ─────────────────────────────────────────────────────────────
  const validar = () => {
    const e = { categoria: '', arquivo: '', titulo: '', periodo: '' }
    if (!categoriaId)    e.categoria = 'Selecione a categoria da atividade.'
    if (!arquivo)        e.arquivo   = 'Selecione o ficheiro do certificado.'
    if (!titulo.trim())  e.titulo    = 'Informe o título da atividade.'
    if (!periodo.trim()) e.periodo   = 'Informe o período de realização.'
    setErros(e)
    return !e.categoria && !e.arquivo && !e.titulo && !e.periodo
  }

  // ── Envio ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (ev) => {
    ev.preventDefault()
    if (!validar()) return

    const formData = new FormData()
    formData.append('categoria', categoriaId)
    formData.append('arquivo_pdf', arquivo)
    formData.append('titulo_atividade', titulo.trim())
    formData.append('periodo_realizacao', periodo.trim())

    try {
      setSubmitting(true)
      await certificadosService.criar(formData)
      setSucesso(true)
      toast.success('Certificado enviado com sucesso!', {
        description: 'A coordenação irá analisar o seu documento em breve.',
        duration: 5000,
      })
      setTimeout(() => navigate('/aluno/historico'), 1500)
    } catch (err) {
      const detail =
        err.response?.data?.arquivo_pdf?.[0] ||
        err.response?.data?.categoria?.[0]   ||
        err.response?.data?.detail           ||
        err.friendlyMessage                  ||
        'Erro ao enviar o certificado.'
      toast.error('Falha no envio', { description: detail })
    } finally {
      setSubmitting(false)
    }
  }

  const grupos         = agruparPorEixo(categorias)
  const catSelecionada = categorias.find(c => String(c.id) === String(categoriaId))

  return (
    <div className="min-h-screen bg-bg flex flex-col">

      {/* ── Barra de topo ─────────────────────────────────────────────────── */}
      <header className="h-14 bg-bg-surface border-b border-border flex items-center gap-4 px-4 shrink-0">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-label text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </button>
        <span className="text-border">|</span>
        <span className="text-label font-bold text-text-primary">Enviar Certificado AACC</span>
      </header>

      {/* ── Corpo centrado ────────────────────────────────────────────────── */}
      <div className="flex-1 flex items-start justify-center p-6">
        <div className="w-full max-w-2xl space-y-5">

          {sucesso ? (
            /* ─ Banner de sucesso ─ */
            <div className="surface rounded-sm border-2 border-success bg-success-light/40 p-12 flex flex-col items-center gap-4 text-center">
              <div className="h-14 w-14 rounded-full bg-success/20 flex items-center justify-center">
                <CheckCircle2 className="h-8 w-8 text-success" />
              </div>
              <div>
                <p className="text-h4 font-bold text-success">Certificado enviado!</p>
                <p className="text-label text-text-secondary mt-1">Redirecionando para o seu histórico...</p>
              </div>
              <Loader2 className="h-5 w-5 animate-spin text-success" />
            </div>
          ) : (

            <form onSubmit={handleSubmit} className="surface rounded-sm border border-border overflow-hidden">

              {/* Cabeçalho do card */}
              <div className="px-6 py-4 border-b border-border bg-bg flex items-center gap-3">
                <div className="h-9 w-9 rounded-sm bg-primary/10 flex items-center justify-center shrink-0">
                  <FolderOpen className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h1 className="text-label font-bold text-text-primary">Novo Certificado</h1>
                  <p className="text-helper text-text-secondary">
                    Preencha os campos e anexe o comprovante.
                  </p>
                </div>
              </div>

              <div className="p-6 space-y-6">

                {/* ── Categoria ──────────────────────────────────────── */}
                <div>
                  <label
                    htmlFor="categoria-select"
                    className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5"
                  >
                    <Layers className="h-4 w-4 text-text-secondary" />
                    Categoria da Atividade <span className="text-danger">*</span>
                  </label>

                  {loadingCats ? (
                    <div className="h-10 rounded-xs border border-border bg-bg animate-pulse" />
                  ) : erroCats ? (
                    <p className="flex items-center gap-1.5 text-helper text-danger">
                      <AlertTriangle className="h-3.5 w-3.5" /> {erroCats}
                    </p>
                  ) : (
                    <select
                      id="categoria-select"
                      value={categoriaId}
                      onChange={(e) => {
                        setCategoriaId(e.target.value)
                        setErros(prev => ({ ...prev, categoria: '' }))
                      }}
                      className={cn(
                        'w-full h-10 rounded-xs border px-3 text-label bg-bg focus:ring-2 focus:ring-primary outline-none transition-shadow',
                        erros.categoria ? 'border-danger' : 'border-border',
                        !categoriaId && 'text-text-disabled',
                      )}
                    >
                      <option value="" disabled>Selecione a categoria...</option>
                      {Object.entries(grupos).map(([eixo, cats]) => (
                        <optgroup key={eixo} label={`── ${eixo}`}>
                          {cats.map(cat => (
                            <option key={cat.id} value={cat.id}>
                              {cat.nome}{cat.limite_maximo_horas && cat.limite_maximo_horas !== 9999 ? ` (teto: ${cat.limite_maximo_horas}h)` : ''}
                            </option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                  )}

                  {erros.categoria && (
                    <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {erros.categoria}
                    </p>
                  )}
                  {catSelecionada && (
                    <div className="mt-1.5 flex flex-col gap-0.5">
                      {catSelecionada.limite_maximo_horas && catSelecionada.limite_maximo_horas !== 9999 && (
                        <p className="text-helper text-text-secondary">
                          Limite aproveitável nesta categoria:{' '}
                          <span className="font-semibold text-primary">{catSelecionada.limite_maximo_horas}h</span>
                        </p>
                      )}
                      {catSelecionada.limite_por_certificado && (
                        <p className="text-helper text-text-secondary">
                          Limite máximo por certificado:{' '}
                          <span className="font-semibold text-primary">{catSelecionada.limite_por_certificado}h</span>
                        </p>
                      )}
                    </div>
                  )}

                  {catSelecionada?.tooltip_display && (
                    <div className="mt-3 flex gap-2.5 rounded-sm border border-primary-muted bg-primary-light/80 p-3 text-primary-hover">
                      <Info className="h-4 w-4 shrink-0 mt-0.5 text-primary" />
                      <p className="text-helper font-medium leading-relaxed">
                        {catSelecionada.tooltip_display}
                      </p>
                    </div>
                  )}
                </div>

                {/* ── Upload ──────────────────────────────────────────── */}
                <div>
                  <label className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5">
                    <Upload className="h-4 w-4 text-text-secondary" />
                    Ficheiro do Certificado <span className="text-danger">*</span>
                  </label>

                  <DropZone
                    arquivo={arquivo}
                    onChange={handleArquivo}
                    erro={erros.arquivo}
                    analisando={analisando}
                  />

                  {arquivo && !analisando && (
                    <button
                      type="button"
                      onClick={() => {
                        setArquivo(null)
                        setTitulo('')
                        setPeriodo('')
                        setCoPilotoUsado(false)
                      }}
                      className="mt-1.5 flex items-center gap-1 text-helper text-text-secondary hover:text-danger transition-colors"
                    >
                      <X className="h-3.5 w-3.5" /> Remover ficheiro
                    </button>
                  )}
                </div>

                {/* ── Callout do Copiloto ──────────────────────────────── */}
                {coPilotoUsado && (
                  leituraImagem ? (
                    // Alerta severo para imagens/PDFs escaneados
                    <div className="flex gap-2.5 rounded-sm border border-orange-400 bg-orange-50 p-3 text-orange-900">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-orange-500" />
                      <p className="text-helper font-medium leading-relaxed">
                        <span className="font-bold">Atenção: Este documento é uma imagem ou PDF escaneado.</span>{' '}
                        A leitura automática pode conter falhas de reconhecimento.{' '}
                        <span className="font-bold">Revise o Título e a Data com atenção redobrada antes de enviar.</span>
                      </p>
                    </div>
                  ) : (
                    // Alerta discreto para PDFs com camada de texto
                    <div className="flex gap-2.5 rounded-sm border border-amber-300 bg-amber-50 p-3 text-amber-800">
                      <Sparkles className="h-4 w-4 shrink-0 mt-0.5 text-amber-500" />
                      <p className="text-helper font-medium leading-relaxed">
                        Extraímos esses dados automaticamente do seu certificado.{' '}
                        <span className="font-bold">Por favor, revise-os antes de enviar.</span>
                      </p>
                    </div>
                  )
                )}

                {/* ── Título da Atividade ──────────────────────────────── */}
                <div>
                  <label
                    htmlFor="titulo-input"
                    className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5"
                  >
                    <Type className="h-4 w-4 text-text-secondary" />
                    Título da Atividade <span className="text-danger">*</span>
                    {analisando && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary ml-1" />}
                  </label>
                  <input
                    id="titulo-input"
                    type="text"
                    value={titulo}
                    onChange={(e) => {
                      setTitulo(e.target.value)
                      setErros(prev => ({ ...prev, titulo: '' }))
                    }}
                    placeholder="Ex: Curso de Metodologia Ativa em EAD"
                    disabled={analisando}
                    className={cn(
                      'w-full h-10 rounded-xs border px-3 text-label bg-bg focus:ring-2 focus:ring-primary outline-none transition-shadow disabled:opacity-50',
                      erros.titulo ? 'border-danger' : 'border-border',
                    )}
                  />
                  {erros.titulo && (
                    <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {erros.titulo}
                    </p>
                  )}
                </div>

                {/* ── Período de Realização ────────────────────────────── */}
                <div>
                  <label
                    htmlFor="periodo-input"
                    className="text-label font-semibold text-text-primary mb-1.5 flex items-center gap-1.5"
                  >
                    <Calendar className="h-4 w-4 text-text-secondary" />
                    Período de Realização <span className="text-danger">*</span>
                    {analisando && <Loader2 className="h-3.5 w-3.5 animate-spin text-primary ml-1" />}
                  </label>
                  <input
                    id="periodo-input"
                    type="text"
                    value={periodo}
                    onChange={(e) => {
                      setPeriodo(e.target.value)
                      setErros(prev => ({ ...prev, periodo: '' }))
                    }}
                    placeholder="Ex: Janeiro/2025 ou 10/01/2025 a 15/03/2025"
                    disabled={analisando}
                    className={cn(
                      'w-full h-10 rounded-xs border px-3 text-label bg-bg focus:ring-2 focus:ring-primary outline-none transition-shadow disabled:opacity-50',
                      erros.periodo ? 'border-danger' : 'border-border',
                    )}
                  />
                  {erros.periodo && (
                    <p className="flex items-center gap-1.5 text-helper text-danger mt-1.5">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {erros.periodo}
                    </p>
                  )}
                </div>

                {/* ── Botões ──────────────────────────────────────────── */}
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => navigate(-1)}
                    className="flex-1 h-10 rounded-xs border border-border text-label font-medium text-text-secondary hover:bg-bg transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    id="btn-enviar"
                    type="submit"
                    disabled={submitting || loadingCats || analisando}
                    className={cn(
                      'flex-1 h-10 rounded-xs text-white font-semibold text-label transition-colors flex items-center justify-center gap-2',
                      submitting || loadingCats || analisando
                        ? 'bg-primary/60 cursor-not-allowed'
                        : 'bg-primary hover:bg-primary-hover',
                    )}
                  >
                    {submitting
                      ? <><Loader2 className="h-4 w-4 animate-spin" /> A enviar...</>
                      : <><Upload className="h-4 w-4" /> Enviar Certificado</>}
                  </button>
                </div>

              </div>
            </form>
          )}

          {/* ── Dica de uso ───────────────────────────────────────────── */}
          {!sucesso && (
            <div className="rounded-xs border border-border bg-bg-surface p-4 flex items-start gap-3">
              <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="text-helper font-semibold text-text-primary mb-1">Como funciona?</p>
                <ol className="text-helper text-text-secondary space-y-0.5 list-decimal list-inside">
                  <li>Selecione a categoria da atividade realizada.</li>
                  <li>Anexe o comprovante — o Copiloto preenche título e período automaticamente.</li>
                  <li>Revise os dados extraídos e corrija se necessário.</li>
                  <li>A coordenação revisa e defere ou indefere o documento.</li>
                </ol>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
