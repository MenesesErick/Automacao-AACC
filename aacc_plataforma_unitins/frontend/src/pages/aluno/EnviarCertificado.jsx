import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Button } from '@/components/atoms/Button'
import { UploadCloud, File, X, Info, CheckCircle, AlertCircle, Cpu } from 'lucide-react'
import { categoriasService, certificadosService } from '@/services/api/endpoints'
import { useAuth } from '@/contexts/AuthContext'

export default function EnviarCertificado() {
  const { user } = useAuth()

  const [file, setFile]               = useState(null)
  const [dragging, setDragging]       = useState(false)
  const [categoria, setCategoria]     = useState('')
  const [categorias, setCategorias]   = useState([])
  const [loadingCats, setLoadingCats] = useState(true)
  const [submitting, setSubmitting]   = useState(false)
  const [resultado, setResultado]     = useState(null) // { type: 'success'|'error', message, ocr? }

  // ── Carrega categorias do banco na montagem ──────────────────────────────
  useEffect(() => {
    async function fetchCategorias() {
      try {
        const { data } = await categoriasService.listar()
        setCategorias(Array.isArray(data) ? data : (data.results ?? []))
      } catch {
        setCategorias([])
      } finally {
        setLoadingCats(false)
      }
    }
    fetchCategorias()
  }, [])

  // ── Handlers de Drag & Drop ──────────────────────────────────────────────
  const handleDragOver  = (e) => { e.preventDefault(); setDragging(true) }
  const handleDragLeave = ()  => setDragging(false)
  const handleDrop      = (e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) setFile(dropped)
  }
  const handleFileChange = (e) => {
    const selected = e.target.files?.[0]
    if (selected) setFile(selected)
  }

  // ── Submit → POST multipart/form-data ────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !categoria) return

    setSubmitting(true)
    setResultado(null)

    const formData = new FormData()
    formData.append('arquivo_pdf', file)
    formData.append('categoria', categoria)
    // horas_declaradas NÃO é enviado — o OCR extrai automaticamente

    try {
      const { data } = await certificadosService.criar(formData)

      // O OCR já rodou no backend — mostra o resultado da "sugestão da IA"
      const horasOCR    = data.horas_declaradas ?? 0
      const confianca   = data.indice_confianca_ocr ?? 0
      const motivo      = data.motivo_status ?? ''

      setResultado({
        type: 'success',
        message: horasOCR > 0
          ? `Documento enviado e processado pelo OCR! Detectadas ${horasOCR}h (confiança: ${Number(confianca).toFixed(0)}%). Aguarda revisão do coordenador.`
          : `Documento enviado! O OCR não localizou as horas automaticamente — será revisto manualmente pelo coordenador. (${motivo})`,
        horasOCR,
        confianca,
      })

      // Limpa o formulário
      setFile(null)
      setCategoria('')
    } catch (err) {
      const msg = err.friendlyMessage ?? 'Erro ao enviar. Verifique os dados e tente novamente.'
      setResultado({ type: 'error', message: msg })
    } finally {
      setSubmitting(false)
    }
  }

  const isFormValido = file && categoria

  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Portal do Aluno</p>
          <h1 className="text-h3 font-bold text-text-primary">Enviar Certificado</h1>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-6">

        {/* Feedback de resultado */}
        {resultado && (
          <div className={`rounded-sm p-4 flex items-start gap-3 ${
            resultado.type === 'success'
              ? 'bg-success-light border border-success-muted text-success'
              : 'bg-danger-light border border-danger-muted text-danger'
          }`}>
            {resultado.type === 'success'
              ? <CheckCircle className="h-5 w-5 shrink-0 mt-0.5" />
              : <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            }
            <div>
              <p className="text-label">{resultado.message}</p>
              {resultado.type === 'success' && (
                <p className="text-helper mt-1 opacity-80">
                  O documento encontra-se em <strong>Revisão Manual</strong> — o coordenador terá a palavra final sobre as horas aprovadas.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Informações do documento */}
        <div className="surface rounded-sm p-6">
          <h2 className="text-card font-semibold text-text-primary mb-4">Informações do Documento</h2>
          <div className="space-y-4">

            {/* Categoria */}
            <div>
              <label htmlFor="categoria" className="text-label font-medium text-text-primary mb-1.5 block">
                Categoria da AACC <span className="text-danger">*</span>
              </label>
              <select
                id="categoria"
                className="w-full rounded-xs border border-border bg-bg-surface text-text-primary h-10 px-3 focus:outline-none focus:ring-2 focus:ring-primary shadow-xs disabled:opacity-50"
                value={categoria}
                onChange={(e) => setCategoria(e.target.value)}
                disabled={loadingCats}
                required
              >
                <option value="">
                  {loadingCats ? 'Carregando categorias...' : 'Selecione uma categoria...'}
                </option>
                {categorias.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    [{cat.eixo}] {cat.nome} — até {cat.limite_maximo_horas}h
                  </option>
                ))}
              </select>
            </div>

            {/* Banner informativo — sem campo de horas */}
            <div className="bg-primary-light border border-primary-muted rounded-xs p-3 flex gap-2 text-primary">
              <Cpu className="h-4 w-4 shrink-0 mt-0.5" />
              <p className="text-helper">
                <strong>Motor de OCR activo:</strong> As horas serão extraídas automaticamente do seu documento.
                Não é necessário informá-las manualmente.
              </p>
            </div>
          </div>
        </div>

        {/* Upload */}
        <div className="surface rounded-sm p-6">
          <h2 className="text-card font-semibold text-text-primary mb-4">Anexar Arquivo</h2>

          {!file ? (
            <div
              role="button"
              tabIndex={0}
              className={`border-2 border-dashed rounded-sm p-8 text-center cursor-pointer transition-colors ${
                dragging
                  ? 'border-primary bg-primary-light'
                  : 'border-border hover:border-border-strong hover:bg-bg'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-upload').click()}
              onKeyDown={(e) => e.key === 'Enter' && document.getElementById('file-upload').click()}
            >
              <UploadCloud className={`h-10 w-10 mx-auto mb-3 ${dragging ? 'text-primary' : 'text-text-disabled'}`} />
              <p className="text-label text-text-primary font-medium mb-1">
                Clique para fazer upload ou arraste o ficheiro PDF
              </p>
              <p className="text-helper text-text-secondary">PDF — máximo 5 MB</p>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept="application/pdf"
                onChange={handleFileChange}
              />
            </div>
          ) : (
            <div className="border border-border rounded-sm p-4 flex items-center gap-4 bg-bg">
              <div className="h-10 w-10 bg-primary-light text-primary rounded-xs flex items-center justify-center shrink-0">
                <File className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-label font-medium text-text-primary truncate">{file.name}</p>
                <p className="text-helper text-text-secondary">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="p-2 text-text-secondary hover:text-danger transition-colors rounded-xs"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        {/* Aviso de fluxo */}
        <div className="bg-primary-light border border-primary-muted rounded-sm p-4 flex gap-3 text-primary">
          <Info className="h-5 w-5 shrink-0 mt-0.5" />
          <div className="text-helper">
            <strong>Como funciona:</strong> Após o envio, o OCR extrai as horas do PDF automaticamente
            e o documento vai para fila de <strong>Revisão Manual</strong>. O coordenador valida
            a sugestão e tem a palavra final sobre as horas aprovadas.
          </div>
        </div>

        {/* Botões */}
        <div className="flex justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="secondary"
            size="lg"
            onClick={() => { setFile(null); setCategoria(''); setResultado(null) }}
            disabled={submitting}
          >
            Limpar
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            loading={submitting}
            disabled={!isFormValido || submitting}
          >
            {submitting ? 'A processar OCR...' : 'Enviar para Análise'}
          </Button>
        </div>
      </form>
    </AppLayout>
  )
}
