import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Button } from '@/components/atoms/Button'
import { Input } from '@/components/atoms/Input'
import { UploadCloud, File, X, Info } from 'lucide-react'

export default function EnviarCertificado() {
  const [file, setFile] = useState(null)
  const [categoria, setCategoria] = useState('')
  const [horas, setHoras] = useState('')

  const handleDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files?.length > 0) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files?.length > 0) {
      setFile(e.target.files[0])
    }
  }

  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Portal do Aluno</p>
          <h1 className="text-h3 font-bold text-text-primary">Enviar Certificado</h1>
        </div>
      }
    >
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="surface rounded-sm p-6">
          <h2 className="text-card font-semibold text-text-primary mb-4">Informações do Documento</h2>
          
          <div className="space-y-4">
            <div>
              <label className="text-label font-medium text-text-primary mb-1 block">Categoria da AACC</label>
              <select 
                className="w-full rounded-xs border border-border bg-bg-surface text-text-primary h-10 px-3 focus:outline-none focus:ring-2 focus:ring-primary shadow-xs"
                value={categoria}
                onChange={(e) => setCategoria(e.target.value)}
              >
                <option value="">Selecione uma categoria...</option>
                <option value="1">Monitoria (Ensino)</option>
                <option value="2">Iniciação Científica (Pesquisa)</option>
                <option value="3">Estágio Extracurricular (Extensão)</option>
              </select>
            </div>

            <Input 
              label="Carga Horária Declarada no Certificado (horas)"
              type="number" 
              placeholder="Ex: 40"
              value={horas}
              onChange={(e) => setHoras(e.target.value)}
            />
          </div>
        </div>

        <div className="surface rounded-sm p-6">
          <h2 className="text-card font-semibold text-text-primary mb-4">Anexar Arquivo</h2>
          
          {!file ? (
            <div 
              className="border-2 border-dashed border-border rounded-sm p-8 text-center hover:bg-bg transition-colors cursor-pointer"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-upload').click()}
            >
              <UploadCloud className="h-10 w-10 text-text-disabled mx-auto mb-3" />
              <p className="text-label text-text-primary font-medium mb-1">Clique para fazer upload ou arraste o ficheiro PDF</p>
              <p className="text-helper text-text-secondary">Tamanho máximo: 5MB</p>
              <input 
                id="file-upload" 
                type="file" 
                className="hidden" 
                accept="application/pdf,image/png,image/jpeg"
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
                <p className="text-helper text-text-secondary">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <button 
                onClick={() => setFile(null)}
                className="p-2 text-text-secondary hover:text-danger transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        <div className="bg-primary-light border border-primary-muted rounded-sm p-4 flex gap-3 text-primary">
          <Info className="h-5 w-5 shrink-0 mt-0.5" />
          <div className="text-helper">
            <strong>Atenção:</strong> O documento será lido automaticamente pela nossa IA de OCR. 
            Certifique-se de que a imagem ou PDF está legível e não contém rasuras.
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="secondary" size="lg">Cancelar</Button>
          <Button variant="primary" size="lg" disabled={!file || !categoria || !horas}>Enviar para Validação Automática</Button>
        </div>
      </div>
    </AppLayout>
  )
}
