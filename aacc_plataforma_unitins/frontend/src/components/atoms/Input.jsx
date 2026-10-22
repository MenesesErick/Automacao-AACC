import { forwardRef } from 'react'
import { cn } from '@/utils/cn'

/**
 * Átomo Input com suporte a label, helper text, erro, ícones e estados.
 */
export const Input = forwardRef(function Input(
  {
    label,
    helperText,
    error,
    leftIcon,
    rightIcon,
    size = 'md',
    fullWidth = false,
    className,
    id,
    ...props
  },
  ref,
) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-')

  const sizes = {
    sm: 'h-8  text-label px-3',
    md: 'h-10 text-label px-3',
    lg: 'h-10 text-body  px-4',
  }

  return (
    <div className={cn('flex flex-col', fullWidth && 'w-full')}>
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-text-primary">
          {label}
        </label>
      )}

      <div className="relative flex items-center">
        {leftIcon && (
          <span className="absolute left-3 text-text-secondary flex items-center pointer-events-none">
            {leftIcon}
          </span>
        )}

        <input
          ref={ref}
          id={inputId}
          {...props}
          className={cn(
            'w-full rounded-xs border bg-white text-text-primary placeholder:text-text-disabled',
            'transition-colors duration-normal',
            'focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20',
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-bg',
            sizes[size],
            leftIcon  && 'pl-9',
            rightIcon && 'pr-9',
            error
              ? 'border-danger text-danger focus:border-danger focus:ring-danger/20'
              : 'border-border-strong hover:border-text-disabled',
            className,
          )}
        />

        {rightIcon && (
          <span className="absolute right-3 text-text-secondary flex items-center">
            {rightIcon}
          </span>
        )}
      </div>

      {(helperText || error) && (
        <p className={cn('mt-1 text-helper', error ? 'text-danger' : 'text-text-secondary')}>
          {error ?? helperText}
        </p>
      )}
    </div>
  )
})
