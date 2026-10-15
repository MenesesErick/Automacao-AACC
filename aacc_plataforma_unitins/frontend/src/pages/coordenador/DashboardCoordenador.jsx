import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { ShieldAlert, Users, CheckCircle, Search, FileText, ArrowRight, Loader2 } from 'lucide-react'
import { certificadosService, alunoService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'
import { DashboardHero } from '@/components/organisms/DashboardHero'

export default function DashboardCoordenador() {
  const navigate = useNavigate()
  const [certificados, setCertificados] = useState([])
  const [alunos, setAlunos] = useState([])
  const [loading, setLoading] = useState(true)
  const [buscaAluno, setBuscaAluno] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        const [resCerts, resAlunos] = await Promise.all([
          certificadosService.listar(),
          alunoService.listarAlunos()
        ])
        const certsData = Array.isArray(resCerts.data) ? resCerts.data : (resCerts.data.results || [])
        const alunosData = Array.isArray(resAlunos.data) ? resAlunos.data : (resAlunos.data.results || [])
        
        setCertificados(certsData)
        setAlunos(alunosData)
      } catch (err) {
        console.error('Erro ao carregar dashboard', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  // Processamento
  const pendentes = certificados.filter(c => c.status === 'revisao_manual' || c.status === 'pendente_ocr')
  
  // Contagem de alunos
  const totalAlunos = alunos.length
  
  const alunosElegiveis = alunos.filter(a => {
    const computadas = parseFloat(a.horas_aprovadas || 0)
    const meta = parseFloat(a.meta_horas || 120)
    return computadas >= meta && meta > 0
  }).length

  // Filtro de busca de alunos
  const alunosFiltrados = alunos.filter(a => {
    const text = buscaAluno.toLowerCase()
    const nome = (a.aluno_nome || a.nome || a.usuario?.first_name || '').toLowerCase()
    const matricula = (a.matricula || '').toLowerCase()
    return nome.includes(text) || matricula.includes(text)
  })

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString('pt-BR')
  }

  return (
    <AppLayout
      breadcrumb={
        <div>
          <p className="text-helper text-text-secondary">Visão Geral da Coordenação</p>
          <h1 className="text-h3 font-bold text-text-primary">Dashboard Operacional</h1>
        </div>
      }
    >
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-text-secondary">
          <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
          <p>Carregando dados do curso...</p>
        </div>
      ) : (
        <div className="space-y-8">

          {/* Banner institucional */}
          <DashboardHero
            modulo="Coordenação de Curso • Auditoria AACC"
            titulo="Dashboard Operacional da Coordenação"
            descricao="Fila de aprovação de certificados e acompanhamento do progresso dos discentes do seu curso."
          />

          {/* Métricas */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard
              title="Certificados Pendentes"
              value={pendentes.length.toString()}
              icon={<ShieldAlert className="h-5 w-5" />}
              color="danger"
              subtitle="Aguardando validação"
            />
            <StatsCard
              title="Total de Alunos"
              value={totalAlunos.toString()}
              icon={<Users className="h-5 w-5" />}
              color="primary"
              subtitle="Matriculados no curso"
            />
            <StatsCard
              title="Alunos Elegíveis"
              value={alunosElegiveis.toString()}
              icon={<CheckCircle className="h-5 w-5" />}
              color="success"
              subtitle="100% da meta atingida"
            />
          </div>

          {/* Fila de Aprovação */}
          <section className="surface rounded-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-[#F8FAFC] flex items-center justify-between">
              <div>
                <h2 className="text-xs font-extrabold uppercase tracking-wider text-primary flex items-center">
                  <span className="w-1 h-4 bg-gold mr-2 inline-block" />
                  Fila de Aprovação / Auditoria
                </h2>
                <p className="text-helper text-text-secondary mt-1">Certificados aguardando a sua análise</p>
              </div>
              <ShieldAlert className="h-5 w-5 text-danger" />
            </div>
            
            <div className="p-0 overflow-x-auto">
              {pendentes.length === 0 ? (
                <div className="py-12 text-center text-text-secondary">
                  <CheckCircle className="h-10 w-10 text-success/50 mx-auto mb-3" />
                  <p className="text-label font-medium text-text-primary">Fila limpa!</p>
                  <p className="text-helper">Nenhum certificado pendente de análise! 🎉</p>
                </div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-bg border-b border-border text-[11px] uppercase text-text-secondary tracking-wider font-bold">
                      <th className="px-5 py-3">Aluno</th>
                      <th className="px-5 py-3">Atividade</th>
                      <th className="px-5 py-3">Data Envio</th>
                      <th className="px-5 py-3">Solicitado</th>
                      <th className="px-5 py-3 text-right">Ação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {pendentes.map(cert => (
                      <tr key={cert.id} className="hover:bg-bg-surface transition-colors">
                        <td className="px-5 py-3">
                          <p className="text-sm font-medium text-text-primary">{cert.aluno_nome || '—'}</p>
                          <p className="text-xs text-text-secondary">{cert.aluno_matricula}</p>
                        </td>
                        <td className="px-5 py-3">
                          <p className="text-sm text-text-primary max-w-xs truncate" title={cert.titulo_atividade}>
                            {cert.titulo_atividade || cert.categoria_nome}
                          </p>
                          <p className="text-xs text-text-secondary">{cert.categoria_nome}</p>
                        </td>
                        <td className="px-5 py-3 text-sm text-text-secondary">
                          {formatDate(cert.data_envio)}
                        </td>
                        <td className="px-5 py-3 text-sm font-mono text-text-secondary">
                          {cert.horas_declaradas ? `${cert.horas_declaradas}h` : 'N/A'}
                        </td>
                        <td className="px-5 py-3 text-right">
                          <button
                            onClick={() => navigate(`/coordenador/certificados/${cert.id}`)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-light text-primary hover:bg-primary hover:text-white rounded-xs text-xs font-bold uppercase tracking-wider transition-colors"
                          >
                            Analisar <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>

          {/* Busca de Discentes */}
          <section className="surface rounded-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-border bg-[#F8FAFC] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xs font-extrabold uppercase tracking-wider text-primary flex items-center">
                  <span className="w-1 h-4 bg-gold mr-2 inline-block" />
                  Acompanhamento de Discentes
                </h2>
                <p className="text-helper text-text-secondary mt-1">Acompanhe a evolução de horas dos alunos</p>
              </div>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-disabled" />
                <input
                  type="text"
                  placeholder="Buscar por nome ou matrícula..."
                  value={buscaAluno}
                  onChange={(e) => setBuscaAluno(e.target.value)}
                  className="w-full h-9 pl-9 pr-3 rounded-xs border border-border bg-bg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                />
              </div>
            </div>

            <div className="p-0 overflow-x-auto">
              {alunosFiltrados.length === 0 ? (
                <div className="py-8 text-center text-text-secondary">
                  <p className="text-sm">Nenhum aluno encontrado na busca.</p>
                </div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-bg border-b border-border text-[11px] uppercase text-text-secondary tracking-wider font-bold">
                      <th className="px-5 py-3">Aluno</th>
                      <th className="px-5 py-3">Progresso (Horas)</th>
                      <th className="px-5 py-3 text-right">Ação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {alunosFiltrados.slice(0, 10).map(aluno => {
                      const nome = aluno.aluno_nome || aluno.nome || aluno.usuario?.first_name || 'Desconhecido'
                      const comp = parseFloat(aluno.horas_aprovadas || 0)
                      const meta = parseFloat(aluno.meta_horas || 120)
                      const pct = Math.min(100, Math.round((comp / meta) * 100)) || 0

                      return (
                        <tr key={aluno.id} className="hover:bg-bg-surface transition-colors">
                          <td className="px-5 py-3">
                            <p className="text-sm font-medium text-text-primary">{nome}</p>
                            <p className="text-xs text-text-secondary">{aluno.matricula || 'Sem matrícula'}</p>
                          </td>
                          <td className="px-5 py-3">
                            <div className="flex items-center gap-3">
                              <div className="flex-1 max-w-[200px] h-2.5 bg-gray-200 rounded-xs overflow-hidden">
                                <div 
                                  className={cn("h-full", pct === 100 ? "bg-success" : "bg-primary")} 
                                  style={{ width: `${pct}%` }} 
                                />
                              </div>
                              <span className="text-sm font-mono text-text-secondary whitespace-nowrap">
                                {comp} / {meta}h <span className="text-xs">({pct}%)</span>
                              </span>
                            </div>
                          </td>
                          <td className="px-5 py-3 text-right">
                            <button
                              onClick={() => navigate(`/coordenador/alunos/${aluno.id}`)}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border text-text-secondary hover:bg-bg hover:text-primary rounded-xs text-xs font-bold uppercase tracking-wider transition-colors"
                            >
                              <FileText className="h-3.5 w-3.5" /> Dossier
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
              {alunosFiltrados.length > 10 && (
                <div className="px-5 py-3 border-t border-border text-center">
                  <p className="text-xs text-text-secondary">
                    Mostrando 10 de {alunosFiltrados.length} resultados. Use a busca para refinar.
                  </p>
                </div>
              )}
            </div>
          </section>

        </div>
      )}
    </AppLayout>
  )
}
