import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { Info, BookOpen, Clock, Layers } from 'lucide-react'
import { categoriasService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

export default function RegrasCategorias() {
  const [grupos, setGrupos] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchCategorias() {
      try {
        const { data } = await categoriasService.listar()
        const lista = Array.isArray(data) ? data : (data.results ?? [])
        
        // Agrupar por eixo
        const agrupadas = lista.reduce((acc, cat) => {
          const eixo = cat.eixo_nome || `Eixo #${cat.eixo}`
          if (!acc[eixo]) acc[eixo] = []
          acc[eixo].push(cat)
          return acc
        }, {})
        
        setGrupos(agrupadas)
      } catch (err) {
        console.error('Erro ao buscar categorias:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchCategorias()
  }, [])

  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Informações</p>
          <h1 className="text-h3 font-bold text-text-primary">Regras e Categorias</h1>
        </div>
      }
    >
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Banner Oficial */}
        <div className="bg-primary-light border border-primary-muted rounded-sm p-5 flex items-start gap-4 text-primary">
          <BookOpen className="h-6 w-6 shrink-0 mt-0.5" />
          <div>
            <h2 className="text-label font-bold mb-1">Resolução CONSUNI Nº 057/2025</h2>
            <p className="text-helper leading-relaxed mb-3">
              Consulte o documento oficial da Resolução CONSUNI Nº 057/2025 para mais detalhes técnicos sobre o regulamento de cômputo das Atividades Acadêmico-Científico-Culturais.
            </p>
            <a 
              href="https://www.unitins.br/cms/Arquivos/Download/92D0DB071E550C926A6BCC79FCA42CF7A438D101" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xs text-sm font-semibold hover:bg-primary-hover transition-colors"
            >
              <Info className="h-4 w-4" />
              Acessar Documento Oficial
            </a>
          </div>
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-bg-surface rounded-sm animate-pulse border border-border" />
            ))}
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(grupos).map(([eixo, categorias]) => (
              <section key={eixo}>
                <h3 className="text-h4 font-bold text-text-primary mb-4 flex items-center gap-2 pb-2 border-b border-border">
                  <Layers className="h-5 w-5 text-text-secondary" />
                  Eixo: {eixo}
                </h3>
                
                <div className="grid gap-4">
                  {categorias.map(cat => {
                    const isIlimitado = !cat.limite_maximo_horas || cat.limite_maximo_horas === 9999;
                    return (
                    <div key={cat.id} className="surface rounded-sm border border-border p-5 hover:border-primary-muted transition-colors">
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-3">
                        <h4 className="text-label font-bold text-text-primary">{cat.nome}</h4>
                        
                        <div className="flex flex-wrap items-center gap-3 shrink-0">
                          <span className={cn(
                            "px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5",
                            !isIlimitado ? "bg-primary-light text-primary" : "bg-gray-100 text-gray-600"
                          )}>
                            <Clock className="h-3.5 w-3.5" />
                            Teto Global: {!isIlimitado ? `${cat.limite_maximo_horas}h` : 'Sem limite'}
                          </span>
                          
                          {cat.limite_por_certificado && (
                            <span className="px-2.5 py-1 rounded-full bg-orange-50 text-orange-700 text-xs font-semibold border border-orange-100 flex items-center gap-1.5">
                              Lim. Certificado: {cat.limite_por_certificado}h
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="text-helper text-text-secondary leading-relaxed bg-bg-surface p-3 rounded-xs border border-border">
                        {cat.tooltip_display || cat.tooltip ? (
                          <span className="whitespace-pre-line">{cat.tooltip_display || cat.tooltip}</span>
                        ) : (
                          <span className="italic opacity-70">Sem descrição detalhada.</span>
                        )}
                      </div>
                    </div>
                    )
                  })}
                </div>
              </section>
            ))}
          </div>
        )}

      </div>
    </AppLayout>
  )
}
