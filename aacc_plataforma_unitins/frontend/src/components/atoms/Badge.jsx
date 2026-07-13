import { cn } from '@/utils/cn'

const variants = {
  default: 'bg-bg text-text-secondary border border-border',
  primary: 'bg-primary-light text-primary border border-primary-muted',
  success: 'bg-success-light text-success border border-success-muted',
  warning: 'bg-warning-light text-yellow-700 border border-warning-muted',
  danger:  'bg-danger-light text-danger border border-danger-muted',
  ghost:   'bg-transparent text-text-secondary',
}

const dotColors = {
  default: 'bg-text-disabled',
  primary: 'bg-primary',
  success: 'bg-success',
  warning: 'bg-warning',
  danger:  'bg-danger',
  ghost:   'bg-text-secondary',
}

/**
 * @param {'default'|'primary'|'success'|'warning'|'danger'|'ghost'} [props.variant='default']
 * @param {boolean} [props.dot=false] - mostra indicador colorido
 */
export function Badge({ variant = 'default', dot = false, children, className }) {
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2 py-0.5',
      'rounded-full text-helper font-medium whitespace-nowrap',
      variants[variant],
      className,
    )}>
      {dot && (
        <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColors[variant])} />
      )}
      {children}
    </span>
  )
}
