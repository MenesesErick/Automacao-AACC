import { cn } from '@/utils/cn'

const sizes = {
  xs: 'h-6  w-6  text-[10px]',
  sm: 'h-8  w-8  text-label',
  md: 'h-9  w-9  text-label',
  lg: 'h-10 w-10 text-body',
  xl: 'h-12 w-12 text-card',
}

/**
 * @param {string} [props.src] - URL da imagem
 * @param {string} [props.name] - Fallback iniciais (ex: "João Silva" → "JS")
 * @param {'xs'|'sm'|'md'|'lg'|'xl'} [props.size='md']
 * @param {boolean} [props.online] - Indicador de presença
 */
export function Avatar({ src, name, size = 'md', online, className }) {
  const initials = name
    ?.split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <div className={cn('relative shrink-0', className)}>
      {src ? (
        <img
          src={src}
          alt={name ?? 'Avatar'}
          className={cn('rounded-full object-cover', sizes[size])}
        />
      ) : (
        <div className={cn(
          'rounded-full flex items-center justify-center font-semibold',
          'bg-primary-light text-primary border border-primary-muted',
          sizes[size],
        )}>
          {initials ?? '?'}
        </div>
      )}
      {online !== undefined && (
        <span className={cn(
          'absolute bottom-0 right-0 rounded-full border-2 border-bg-surface',
          'h-2.5 w-2.5',
          online ? 'bg-success' : 'bg-text-disabled',
        )} />
      )}
    </div>
  )
}
