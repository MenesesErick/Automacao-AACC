import { cn } from '@/utils/cn'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

/**
 * Card de métrica/KPI para o Dashboard.
 *
 * @param {string} title
 * @param {string|number} value
 * @param {string} [subtitle]
 * @param {React.ReactNode} [icon]
 * @param {'up'|'down'|'neutral'} [trend]
 * @param {string} [trendLabel]
 * @param {'primary'|'success'|'warning'|'danger'|'default'} [color='default']
 */
export function StatsCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendLabel,
  color = 'default',
  className,
}) {
  const iconBg = {
    default: 'bg-bg text-text-secondary border border-border',
    primary: 'bg-primary-light text-primary border border-primary-muted',
    success: 'bg-success-light text-success border border-success/30',
    warning: 'bg-gold-light text-[#B45309] border border-gold/40',
    danger:  'bg-danger-light text-danger border border-danger/30',
  }[color]

  const TrendIcon = { up: TrendingUp, down: TrendingDown, neutral: Minus }[trend] ?? null
  const trendColor = { up: 'text-success', down: 'text-danger', neutral: 'text-text-secondary' }[trend] ?? ''

  return (
    <div className={cn('surface rounded-xs p-5 border-l-4 border-l-primary flex flex-col gap-4', className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-bold uppercase tracking-wider text-text-secondary truncate">{title}</p>
        </div>
        {icon && (
          <div className={cn('h-11 w-11 rounded-xs flex items-center justify-center shrink-0', iconBg)}>
            {icon}
          </div>
        )}
      </div>

      <div>
        <p className="text-2xl font-extrabold text-primary leading-none">{value}</p>
        {subtitle && (
          <p className="text-helper text-text-secondary mt-1.5">{subtitle}</p>
        )}
      </div>

      {trend && trendLabel && (
        <div className={cn('flex items-center gap-1', trendColor)}>
          {TrendIcon && <TrendIcon className="h-3.5 w-3.5 shrink-0" />}
          <span className="text-helper font-medium">{trendLabel}</span>
        </div>
      )}
    </div>
  )
}
