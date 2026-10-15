/**
 * Componentes visuais reutilizáveis para o Extrato do Aluno (RN02).
 * Usados tanto no DashboardAluno (visão própria) quanto no
 * AlunoRaioXDrawer (visão do Coordenador).
 */
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadialBarChart, RadialBar, PolarAngleAxis
} from 'recharts'
import { Info, PartyPopper, TriangleAlert } from 'lucide-react'

// ── Design System cores ───────────────────────────────────────────────────────
export const CORES = {
  primary: '#003366',
  success: '#166534',
  warning: '#B45309',
  danger:  '#B91C1C',
  muted:   '#E5E7EB',
  text:    '#4B5563',
}

export const COR_EIXO = {
  Ensino:   '#003366',
  Pesquisa: '#F5A623',
  Extensao: '#166534',
}

// ── Tooltip customizado ───────────────────────────────────────────────────────
export function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-border rounded-xs shadow-md px-3 py-2">
      <p className="text-helper font-semibold text-text-primary">{label}</p>
      <p className="text-label font-bold" style={{ color: payload[0]?.fill }}>
        {payload[0]?.value}h
      </p>
    </div>
  )
}

// ── Banner de Aptidão à Formatura ─────────────────────────────────────────────
export function BannerFormatura({ extrato, loading, compact = false }) {
  if (loading) {
    return <div className="rounded-xs p-4 mb-4 animate-pulse h-14 bg-border" />
  }
  if (!extrato) return null

  const { apto_formatura, faltam_horas, faltam_eixos } = extrato

  if (apto_formatura) {
    return (
      <div className="flex items-center gap-3 rounded-xs p-4 mb-4 bg-success-light border border-success/40 border-l-4 border-l-gold">
        <div className="h-11 w-11 rounded-xs bg-gold-light border border-gold/40 flex items-center justify-center shrink-0">
          <PartyPopper className="h-5 w-5 text-[#B45309]" />
        </div>
        <div>
          <p className="text-xs font-extrabold uppercase tracking-wider text-success">
            {compact ? 'Apto para formatura!' : 'Elegível ao Anexo I — requisitos de AACC cumpridos'}
          </p>
          {!compact && (
            <p className="text-helper text-success/80 mt-0.5">
              Você pode solicitar a geração do Anexo I para entrega na Secretaria Acadêmica.
            </p>
          )}
        </div>
      </div>
    )
  }

  const partes = []
  if (faltam_horas > 0) partes.push(`${faltam_horas}h`)
  if (faltam_eixos > 0) partes.push(`${faltam_eixos} eixo(s)`)

  return (
    <div className="flex items-start gap-3 rounded-xs p-4 mb-4 bg-warning-light border border-warning-muted border-l-4 border-l-warning">
      <TriangleAlert className="h-5 w-5 text-warning shrink-0 mt-0.5" />
      <div>
        <p className="text-xs font-extrabold uppercase tracking-wider text-warning">Requisitos não cumpridos</p>
        {!compact && (
          <p className="text-helper text-warning mt-0.5">
            {partes.length > 0
              ? `Faltam ${partes.join(' e ')} — exige ≥ 2 eixos distintos.`
              : 'Verifique as condições com o coordenador.'}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Gráfico Radial de Progresso ───────────────────────────────────────────────
export function GraficoProgresso({ pct, horasAprovadas, meta }) {
  const data = [{ value: pct, fill: pct >= 100 ? CORES.success : CORES.primary }]
  return (
    <div className="surface rounded-xs p-5 flex flex-col items-center justify-center gap-2">
      <p className="text-[11px] text-text-secondary font-bold uppercase tracking-wider self-start">
        Progresso Geral
      </p>
      <div className="relative w-full max-w-[180px] mx-auto" style={{ height: 180 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%" cy="50%"
            innerRadius="68%" outerRadius="90%"
            startAngle={90} endAngle={-270}
            data={data}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar dataKey="value" cornerRadius={2} background={{ fill: CORES.muted }} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-h3 font-extrabold text-primary tabular-nums">{pct}%</span>
          <span className="text-helper text-text-secondary">{horasAprovadas}h / {meta}h</span>
        </div>
      </div>
    </div>
  )
}

// ── Gráfico de Barras por Eixo ────────────────────────────────────────────────
export function GraficoEixos({ horas_por_eixo, meta }) {
  const safeEixos = horas_por_eixo ?? {}
  const data = Object.entries(safeEixos).map(([eixo, horas]) => ({
    eixo,
    horas,
    fill: COR_EIXO[eixo] ?? CORES.primary,
  }))

  const maxValue = Math.max(meta, ...Object.values(safeEixos), 0) + 10

  return (
    <div className="surface rounded-xs p-5 flex flex-col gap-3 flex-1">
      <div className="flex items-center justify-between">
        <p className="text-[11px] text-text-secondary font-bold uppercase tracking-wider">
          Horas por Eixo (RN02)
        </p>
        <div className="flex items-center gap-1 text-helper text-text-secondary">
          <Info className="h-3.5 w-3.5" />
          <span>≥ 2 eixos para formatura</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} barSize={36} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CORES.muted} vertical={false} />
          <XAxis dataKey="eixo" tick={{ fontSize: 12, fill: CORES.text }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: CORES.text }} axisLine={false} tickLine={false} domain={[0, maxValue]} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#F7F9FC' }} />
          <Bar dataKey="horas" radius={[2, 2, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="space-y-3 pt-1">
        {data.map((d) => {
          const pctEixo = meta > 0 ? Math.min(100, Math.round((d.horas / meta) * 100)) : 0
          return (
            <div key={d.eixo}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-text-secondary">{d.eixo}</span>
                <span className="text-helper text-text-secondary">
                  <strong className="text-text-primary">{d.horas}h</strong> · {pctEixo}% da meta total
                </span>
              </div>
              <div className="h-2.5 rounded-xs bg-gray-200 overflow-hidden">
                <div
                  className={pctEixo >= 100 ? 'h-full bg-success' : 'h-full bg-primary'}
                  style={{ width: `${pctEixo}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
