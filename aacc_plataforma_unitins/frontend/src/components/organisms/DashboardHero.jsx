import { cn } from '@/utils/cn'

/**
 * Banner de contexto institucional (Unitins / DSGOV) para o topo dos dashboards.
 *
 * @param {string} modulo   Pill superior em caixa alta (ex.: "PORTAL DO DISCENTE • ...")
 * @param {string} titulo   Título principal
 * @param {string} [descricao]
 * @param {React.ReactNode} [acoes] Ações primárias alinhadas à direita
 */
export function DashboardHero({ modulo, titulo, descricao, acoes, className }) {
  return (
    <div
      className={cn(
        'unitins-hero-pattern rounded-xs p-6 text-white border-b-4 border-gold shadow-xs',
        'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4',
        className,
      )}
    >
      <div className="min-w-0">
        <p className="text-[10px] font-bold uppercase tracking-widest text-gold">{modulo}</p>
        <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white mt-1">{titulo}</h2>
        {descricao && <p className="text-sm text-white/75 mt-1.5 max-w-2xl">{descricao}</p>}
      </div>
      {acoes && <div className="flex flex-wrap items-center gap-2 shrink-0">{acoes}</div>}
    </div>
  )
}

/** Botão de ação primária sobre fundo azul marinho (padrão institucional dourado). */
export const heroActionCls =
  'inline-flex items-center gap-2 bg-gold text-[#0A2540] hover:bg-gold-hover font-extrabold uppercase tracking-wider text-xs px-4 py-2.5 rounded-xs transition-colors'
