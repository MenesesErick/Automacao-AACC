/**
 * DossieAluno.jsx — Dossiê Completo do Aluno (Coordenador)
 *
 * Substitui o AlunoRaioXDrawer por uma página dedicada com:
 *   ┌─ Hero Card ─────────────────────────────────────────────────┐
 *   │  Avatar  |  Nome  |  Matrícula  |  Curso  |  Badge aptidão │
 *   └──────────────────────────────────────────────────────────────┘
 *   ┌─ Progresso (coluna esq) ──┐  ┌─ Horas por Eixo (col dir) ─┐
 *   │  Donut + barra            │  │  Bar chart                  │
 *   └───────────────────────────┘  └─────────────────────────────┘
 *   ┌─ Tabela de Certificados ────────────────────────────────────┐
 *   │  #  Categoria  Horas  Status  Justificativa  →Avaliar       │
 *   └──────────────────────────────────────────────────────────────┘
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, UserCircle, GraduationCap, Hash,
  Mail, Loader2, AlertTriangle, FileText,
  CheckCircle2, XCircle, Clock, Eye,
  ShieldCheck, Award, ShieldAlert, Download,
} from 'lucide-react'
import { toast } from 'sonner'
import { useReactToPrint } from 'react-to-print'
import { cn } from '@/utils/cn'
import { alunoService, certificadosService } from '@/services/api/endpoints'
import { AppLayout } from '@/components/layout/AppLayout'
import { Badge } from '@/components/atoms/Badge'
import {
  BannerFormatura,
  GraficoProgresso,
  GraficoEixos,
} from '@/components/organisms/ExtratoCharts'
import apiClient from '@/services/api/client'
import AnexoIPDF from '@/components/AnexoIPDF'

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_MAP = {
  aprovado:            { label: 'Aprovado',        variant: 'success' },
  pendente_ocr:        { label: 'Pendente OCR',    variant: 'default' },
  revisao_manual:      { label: 'Revisão Manual',  variant: 'warning' },
  rejeitado:           { label: 'Rejeitado',       variant: 'danger'  },
  requerimento_gerado: { label: 'Req. Gerado',     variant: 'primary' },
}

// ─── Barra de progresso inline ───────────────────────────────────────────────

function BarraProgresso({ pct }) {
  return (
    <div className="w-full bg-border rounded-full h-2 overflow-hidden">
      <div
        className={cn(
          'h-2 rounded-full transition-all duration-700',
          pct >= 100 ? 'bg-success' : pct >= 60 ? 'bg-primary' : 'bg-warning',
        )}
        style={{ width: `${Math.min(pct, 100)}%` }}
      />
    </div>
  )
}

// ─── Hero Card do Aluno ───────────────────────────────────────────────────────

function HeroAluno({ extrato, aluno }) {
  const pct  = extrato?.progresso_percentual ?? 0
  const apto = extrato?.apto_formatura ?? false

  return (
    <div className="surface rounded-sm border border-border overflow-hidden">
      {/* Faixa superior colorida */}
      <div className={cn(
        'h-2',
        apto ? 'bg-gradient-to-r from-success to-primary' : 'bg-gradient-to-r from-primary to-primary/40',
      )} />

      <div className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-start gap-5">
          {/* Avatar */}
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center shrink-0 border-2 border-primary/20">
            <UserCircle className="h-9 w-9 text-primary" />
          </div>

          {/* Identidade */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <h1 className="text-h3 font-bold text-text-primary leading-tight">
                {extrato?.aluno_nome ?? aluno?.aluno_nome ?? '—'}
              </h1>
              {apto ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-success/10 border border-success/30 text-helper font-bold text-success">
                  <Award className="h-3 w-3" /> Apto à Formatura
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-warning-light border border-warning-muted text-helper font-bold text-yellow-700">
                  <Clock className="h-3 w-3" /> Em Progresso
                </span>
              )}
            </div>

            {/* Metadados inline */}
            <div className="flex flex-wrap gap-x-5 gap-y-1 mt-2">
              <span className="flex items-center gap-1.5 text-label text-text-secondary">
                <Hash className="h-3.5 w-3.5" />
                {extrato?.matricula ?? aluno?.matricula ?? '—'}
              </span>
              <span className="flex items-center gap-1.5 text-label text-text-secondary">
                <GraduationCap className="h-3.5 w-3.5" />
                {extrato?.curso ?? aluno?.curso ?? '—'}
              </span>
              {aluno?.email && (
                <span className="flex items-center gap-1.5 text-label text-text-secondary">
                  <Mail className="h-3.5 w-3.5" />
                  {aluno.email}
                </span>
              )}
            </div>

            {/* Barra de progresso */}
            <div className="mt-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <p className="text-helper text-text-secondary">
                  Progresso AACC —{' '}
                  <span className="font-semibold text-text-primary">
                    {extrato?.total_horas_aprovadas ?? 0}h
                  </span>{' '}
                  de{' '}
                  <span className="font-semibold text-text-primary">
                    {extrato?.meta_horas ?? '—'}h
                  </span>
                </p>
                <span className={cn(
                  'text-label font-bold',
                  pct >= 100 ? 'text-success' : 'text-primary',
                )}>
                  {pct}%
                </span>
              </div>
              <BarraProgresso pct={pct} />
              {(extrato?.faltam_horas > 0 || extrato?.faltam_eixos > 0) && (
                <p className="text-helper text-text-disabled">
                  {extrato.faltam_horas > 0 && `Faltam ${extrato.faltam_horas}h. `}
                  {extrato.faltam_eixos > 0 && `Precisa de ${extrato.faltam_eixos} eixo(s) adicional(is).`}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Tabela de Certificados ───────────────────────────────────────────────────

function TabelaCertificados({ certs, loading }) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-12 rounded-xs bg-border animate-pulse" />
        ))}
      </div>
    )
  }

  if (!certs.length) {
    return (
      <div className="surface rounded-sm border border-border p-8 text-center">
        <FileText className="h-8 w-8 text-text-disabled mx-auto mb-2" />
        <p className="text-label text-text-secondary">Este aluno ainda não enviou nenhum certificado.</p>
      </div>
    )
  }

  return (
    <div className="surface rounded-sm border border-border overflow-hidden">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-border bg-bg">
            <th className="px-4 py-3 text-helper font-bold text-text-disabled uppercase tracking-wider">#</th>
            <th className="px-4 py-3 text-helper font-bold text-text-disabled uppercase tracking-wider">Categoria</th>
            <th className="px-4 py-3 text-helper font-bold text-text-disabled uppercase tracking-wider">Horas</th>
            <th className="px-4 py-3 text-helper font-bold text-text-disabled uppercase tracking-wider">Status</th>
            <th className="px-4 py-3 text-helper font-bold text-text-disabled uppercase tracking-wider">Data</th>
            <th className="px-4 py-3 text-helper font-bold text-text-disabled uppercase tracking-wider"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {certs.map((cert) => {
            const s = STATUS_MAP[cert.status] ?? { label: cert.status, variant: 'default' }
            const isRejeitado = cert.status === 'rejeitado'
            const isPendente  = ['pendente_ocr', 'revisao_manual'].includes(cert.status)

            return (
              <>
                <tr
                  key={cert.id}
                  onClick={() => navigate(`/coordenador/certificados/${cert.id}`)}
                  className={cn(
                    'group transition-colors cursor-pointer',
                    isRejeitado ? 'bg-danger-light/20 hover:bg-danger-light/50' : 'hover:bg-bg',
                  )}
                >
                  <td className="px-4 py-3">
                    <span className="text-helper text-text-disabled font-mono">#{cert.id}</span>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-label font-medium text-text-primary truncate max-w-[200px]">
                      {cert.categoria_nome ?? '—'}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      'text-label font-bold tabular-nums',
                      cert.status === 'aprovado' ? 'text-success' : 'text-text-primary',
                    )}>
                      {cert.horas_computadas_final != null
                        ? `${cert.horas_computadas_final}h`
                        : `${cert.horas_sugeridas_ia ?? cert.horas_declaradas ?? 0}h`}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={s.variant} dot>{s.label}</Badge>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-helper text-text-disabled">
                      {cert.data_envio
                        ? new Date(cert.data_envio).toLocaleDateString('pt-BR')
                        : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {isPendente ? (
                      <span className="inline-flex items-center gap-1 text-helper font-semibold text-primary">
                        <ShieldAlert className="h-3.5 w-3.5" /> Auditar
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-helper font-medium text-text-secondary">
                        <Eye className="h-3.5 w-3.5" /> Visualizar
                      </span>
                    )}
                  </td>
                </tr>

                {/* Linha extra de justificativa para indeferidos */}
                {isRejeitado && (cert.justificativa_indeferimento || cert.motivo_status) && (
                  <tr key={`${cert.id}-just`} className="bg-danger-light/20">
                    <td colSpan={6} className="px-4 pb-3 pt-0">
                      <div className="flex items-start gap-2 ml-6">
                        <XCircle className="h-3.5 w-3.5 text-danger shrink-0 mt-0.5" />
                        <div>
                          <span className="text-helper font-bold text-danger">Justificativa da Coordenação: </span>
                          <span className="text-helper text-danger/80">
                            {cert.justificativa_indeferimento || cert.motivo_status}
                          </span>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────

export default function DossieAluno() {
  const { id }   = useParams()
  const navigate = useNavigate()

  const [aluno,       setAluno]      = useState(null)
  const [extrato,     setExtrato]    = useState(null)
  const [certs,        setCerts]       = useState([])
  const [loading,      setLoading]     = useState(true)
  const [erro,         setErro]        = useState(null)
  const [gerandoPdf,   setGerandoPdf]  = useState(false)
  const [dadosAnexo,   setDadosAnexo]  = useState(null)

  // ref do componente de impressao (oculto no DOM)
  const anexoRef = useRef(null)

  // react-to-print v3: passa o ref via contentRef; a funcao retornada dispara a impressao
  const handlePrint = useReactToPrint({
    contentRef: anexoRef,
    documentTitle: `Anexo_I_${extrato?.aluno_nome ?? 'Aluno'}`,
    onAfterPrint: () => setGerandoPdf(false),
  })

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setErro(null)

    const fetchTudo = async () => {
      try {
        // Extrato e certificados do aluno em paralelo
        const [resExtrato, resCerts, resAlunos] = await Promise.all([
          alunoService.obterExtrato(id),
          certificadosService.listar(),
          alunoService.listarAlunos(),
        ])

        if (cancelled) return

        const extratoData = resExtrato.data
        setExtrato(extratoData)

        // Localiza o aluno na lista para pegar e-mail
        const listaAlunos = Array.isArray(resAlunos.data) ? resAlunos.data : []
        const alunoEncontrado = listaAlunos.find(a => String(a.id) === String(id))
        setAluno(alunoEncontrado ?? null)

        // Filtra os certificados deste aluno
        const allCerts = Array.isArray(resCerts.data)
          ? resCerts.data
          : (resCerts.data?.results ?? [])
        const certDoAluno = allCerts.filter(c => String(c.aluno) === String(id))
        // Mais recentes primeiro
        certDoAluno.sort((a, b) => new Date(b.data_envio) - new Date(a.data_envio))
        setCerts(certDoAluno)
      } catch (err) {
        if (!cancelled) setErro(err.friendlyMessage ?? 'Erro ao carregar dossiê do aluno.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchTudo()
    return () => { cancelled = true }
  }, [id])

  // ── RN05: Gerar Anexo I — busca JSON, atualiza state e dispara print ────────
  // useEffect aguarda o DOM atualizar antes de chamar handlePrint
  const [printPendente, setPrintPendente] = useState(false)

  useEffect(() => {
    if (printPendente && dadosAnexo) {
      handlePrint()
      setPrintPendente(false)
    }
  }, [printPendente, dadosAnexo, handlePrint])

  const gerarAnexoI = useCallback(async () => {
    setGerandoPdf(true)
    const toastId = toast.loading('Buscando dados do Anexo I...')
    try {
      const response = await apiClient.get(`/academico/alunos/${id}/gerar-anexo-i/`)
      setDadosAnexo(response.data)
      toast.success('Pronto! Abrindo janela de impressao...', { id: toastId })
      setPrintPendente(true)  // dispara o useEffect apos o re-render
    } catch (err) {
      const msg = err?.response?.data?.detail ?? 'Erro ao gerar o Anexo I.'
      toast.error(msg, { id: toastId })
      setGerandoPdf(false)
    }
  }, [id])

  const pct  = extrato?.progresso_percentual ?? 0
  const total = extrato?.total_horas_aprovadas ?? 0
  const meta  = extrato?.meta_horas ?? 120

  // ── Loading global ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <AppLayout breadcrumb={
        <div className="flex items-center gap-2">
          <UserCircle className="h-4 w-4 text-primary" />
          <p className="text-label font-medium text-text-primary">Dossiê do Aluno</p>
        </div>
      }>
        <div className="flex items-center justify-center h-64 gap-3 text-text-secondary">
          <Loader2 className="h-6 w-6 animate-spin" />
          <p className="text-label">Carregando dossiê...</p>
        </div>
      </AppLayout>
    )
  }

  if (erro) {
    return (
      <AppLayout breadcrumb={<p className="text-label font-medium text-text-primary">Dossiê do Aluno</p>}>
        <div className="surface rounded-sm p-6 flex items-center gap-3 text-danger">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <div>
            <p className="text-label font-semibold">Erro ao carregar dados</p>
            <p className="text-helper mt-0.5">{erro}</p>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout
      breadcrumb={
        <div className="min-w-0 flex items-center gap-2">
          <button
            onClick={() => navigate('/coordenador/alunos')}
            className="flex items-center gap-1.5 text-text-secondary hover:text-text-primary transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span className="text-label">Alunos</span>
          </button>
          <span className="text-text-disabled">/</span>
          <p className="text-label font-medium text-text-primary truncate">
            {extrato?.aluno_nome ?? 'Dossiê'}
          </p>
        </div>
      }
    >
      <div className="space-y-6 max-w-6xl">

        {/* ── 1. Hero de Identidade ────────────────────────────────────────── */}
        <HeroAluno extrato={extrato} aluno={aluno} />

        {/* ── 2. Banner de Formatura + Gráficos ───────────────────────────── */}
        <BannerFormatura extrato={extrato} loading={false} />

        <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-4">
          <GraficoProgresso pct={pct} horasAprovadas={total} meta={meta} />
          <GraficoEixos horas_por_eixo={extrato?.horas_por_eixo} meta={meta} />
        </div>

        {/* ── 3. Histórico de Certificados ─────────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-helper font-bold text-text-disabled uppercase tracking-widest">
              Histórico de Certificados ({certs.length})
            </p>
            <div className="flex items-center gap-3">
              <p className="text-helper text-text-disabled">
                {certs.filter(c => c.status === 'aprovado').length} aprovado(s)
                {' · '}
                {certs.filter(c => ['pendente_ocr', 'revisao_manual'].includes(c.status)).length} pendente(s)
              </p>

              {/* Botão RN05 — só aparece quando aluno atingiu 100% */}
              {pct >= 100 && (
                <button
                  id="btn-gerar-anexo-i"
                  onClick={gerarAnexoI}
                  disabled={gerandoPdf}
                  className={cn(
                    'inline-flex items-center gap-2 px-3 py-1.5 rounded-sm text-label font-semibold',
                    'bg-success text-white border border-success/80',
                    'hover:bg-success/90 transition-colors',
                    'disabled:opacity-60 disabled:cursor-not-allowed',
                  )}
                >
                  {gerandoPdf
                    ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    : <Download className="h-3.5 w-3.5" />
                  }
                  {gerandoPdf ? 'Gerando...' : 'Gerar Anexo I (PDF)'}
                </button>
              )}
            </div>
          </div>
          <TabelaCertificados certs={certs} loading={false} />
        </div>

        {/* AnexoIPDF oculto — renderizado para o react-to-print */}
        <div style={{ display: 'none' }}>
          <AnexoIPDF ref={anexoRef} dados={dadosAnexo} />
        </div>

      </div>
    </AppLayout>
  )
}
