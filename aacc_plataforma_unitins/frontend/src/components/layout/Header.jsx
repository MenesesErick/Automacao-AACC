import { cn } from '@/utils/cn'
import { Avatar } from '@/components/atoms/Avatar'
import { useAuth } from '@/contexts/AuthContext'
import { NotificacoesBell } from '@/components/layout/NotificacoesBell'

function roleLabel(role) {
  if (role === 'admin') return 'Administração'
  if (role === 'coordenador') return 'Coordenação'
  return 'Discente'
}

export function Header({ title, breadcrumb, sidebarCollapsed }) {
  const { user } = useAuth()

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-20 flex items-center justify-between gap-4 px-4 sm:px-6',
        'h-16 bg-bg-surface border-b border-border',
        'transition-[left] duration-300',
        sidebarCollapsed ? 'left-16' : 'left-60',
      )}
    >
      <div className="unitins-gold-bar w-full absolute top-0 left-0 right-0" />

      {/* Assinatura oficial UNITINS | seção */}
      <div className="min-w-0 flex items-center">
        <span className="font-extrabold tracking-wider text-primary text-sm uppercase shrink-0">
          UNITINS
        </span>
        <span className="h-4 w-px bg-border-strong mx-2.5 shrink-0" aria-hidden="true" />
        {title ? (
          <h1 className="font-semibold text-text-primary text-sm uppercase tracking-wide truncate">
            {title}
          </h1>
        ) : typeof breadcrumb === 'string' ? (
          <h1 className="font-semibold text-text-primary text-sm uppercase tracking-wide truncate">
            {breadcrumb}
          </h1>
        ) : (
          breadcrumb ?? (
            <h1 className="font-semibold text-text-primary text-sm uppercase tracking-wide truncate">
              AACC Platform
            </h1>
          )
        )}
      </div>

      {/* Usuário e notificações */}
      <div className="flex items-center gap-3 shrink-0">
        <NotificacoesBell />
        <span className="hidden sm:inline-flex rounded-full bg-primary-light text-primary border border-primary-muted px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider">
          {roleLabel(user?.role)}
        </span>
        <Avatar
          name={user?.nome || user?.name || 'U'}
          size="sm"
          online
          className="[&>div]:bg-primary [&>div]:text-white [&>div]:font-bold [&>div]:border-2 [&>div]:border-gold [&>img]:border-2 [&>img]:border-gold"
        />
        <div className="hidden sm:block min-w-0">
          <p className="text-label font-semibold text-text-primary leading-tight truncate max-w-[140px]">
            {user?.nome || user?.name || 'Utilizador'}
          </p>
        </div>
      </div>
    </header>
  )
}
