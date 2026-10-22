import { cn } from '@/utils/cn'

const variants = {
  primary:   'bg-primary text-white border border-transparent hover:bg-primary-hover focus:ring-2 focus:ring-gold/50',
  default:   'bg-primary text-white border border-transparent hover:bg-primary-hover focus:ring-2 focus:ring-gold/50',
  secondary: 'bg-white text-primary border border-primary hover:bg-primary-light font-bold',
  outline:   'bg-white text-primary border border-primary hover:bg-primary-light font-bold',
  gold:      'bg-gold text-sidebar-bg border border-transparent hover:bg-gold-hover font-extrabold',
  danger:    'bg-danger text-white border border-transparent hover:bg-danger-muted',
  ghost:     'bg-transparent text-text-secondary border border-transparent hover:bg-gray-200/60 hover:text-primary',
  success:   'bg-success text-white border border-transparent hover:bg-success-muted',
}

const sizes = {
  xs: 'h-7  px-3 gap-1.5',
  sm: 'h-8  px-3 gap-2',
  md: 'h-9  px-4 gap-2',
  lg: 'h-10 px-5 gap-2',
  xl: 'h-12 px-6 gap-2.5',
}

/**
 * @param {Object} props
 * @param {'primary'|'default'|'secondary'|'outline'|'gold'|'ghost'|'danger'|'success'} [props.variant='primary']
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
        'inline-flex items-center justify-center rounded-xs',
        'font-bold tracking-wider uppercase text-xs',
        'transition-colors duration-normal select-none',
        'focus-visible:outline-none',
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
