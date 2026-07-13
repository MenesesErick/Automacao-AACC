import { cn } from '@/utils/cn'

const variants = {
  primary:   'bg-primary text-text-inverse hover:bg-primary-hover active:bg-secondary shadow-xs',
  secondary: 'bg-bg-surface text-text-primary border border-border hover:bg-bg hover:border-border-strong shadow-xs',
  ghost:     'text-text-secondary hover:text-text-primary hover:bg-bg',
  danger:    'bg-danger text-text-inverse hover:bg-red-700 shadow-xs',
  success:   'bg-success text-text-inverse hover:bg-green-700 shadow-xs',
}

const sizes = {
  xs: 'h-7  px-3 text-helper gap-1.5',
  sm: 'h-8  px-3 text-label gap-2',
  md: 'h-9  px-4 text-label gap-2',
  lg: 'h-10 px-5 text-body  gap-2',
  xl: 'h-12 px-6 text-body  gap-2.5',
}

/**
 * @param {Object} props
 * @param {'primary'|'secondary'|'ghost'|'danger'|'success'} [props.variant='primary']
 * @param {'xs'|'sm'|'md'|'lg'|'xl'} [props.size='md']
 * @param {boolean} [props.loading=false]
 * @param {boolean} [props.fullWidth=false]
 * @param {React.ReactNode} [props.leftIcon]
 * @param {React.ReactNode} [props.rightIcon]
 */
export function Button({
  variant = 'primary',
  size    = 'md',
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  children,
  className,
  disabled,
  ...props
}) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center rounded-xs font-medium',
        'transition-all duration-normal select-none',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        className,
      )}
    >
      {loading ? (
        <svg className="animate-spin h-4 w-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
      ) : leftIcon ? (
        <span className="shrink-0 flex">{leftIcon}</span>
      ) : null}
      {children && <span>{children}</span>}
      {!loading && rightIcon && <span className="shrink-0 flex">{rightIcon}</span>}
    </button>
  )
}
