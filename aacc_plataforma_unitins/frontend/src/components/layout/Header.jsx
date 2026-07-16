import { Bell, Search, Sun } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Avatar } from '@/components/atoms/Avatar'
import { useAuth } from '@/contexts/AuthContext'

export function Header({ breadcrumb, sidebarCollapsed }) {
  const { user } = useAuth()

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-20 flex items-center gap-3 px-4 sm:px-6',
        'h-14 bg-bg-surface/80 border-b border-border backdrop-blur-sm',
        'transition-[left] duration-300',
        sidebarCollapsed ? 'left-16' : 'left-60',
      )}
    >
      {/* Breadcrumb */}
      <div className="flex-1 min-w-0">
        {breadcrumb ?? (
          <p className="text-label text-text-secondary truncate font-medium">AACC Platform</p>
        )}
      </div>

      {/* Barra de pesquisa — só em desktop */}
      <div className="hidden lg:flex items-center gap-2 h-8 px-3 rounded-xs border border-border bg-bg hover:border-border-strong cursor-pointer transition-colors w-48">
        <Search className="h-3.5 w-3.5 text-text-secondary shrink-0" />
        <span className="text-helper text-text-disabled">Pesquisar...</span>
        <kbd className="ml-auto text-helper text-text-disabled bg-bg px-1 py-0.5 rounded border border-border font-mono">
          ⌘K
        </kbd>
      </div>

      {/* Notificações */}
      <button
        className="relative p-2 rounded-xs text-text-secondary hover:text-text-primary hover:bg-bg transition-colors"
        title="Notificações"
      >
        <Bell className="h-4 w-4" />
        <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-danger border-2 border-bg-surface" />
      </button>

      {/* Avatar */}
      <div className="flex items-center gap-2 pl-1 border-l border-border">
        <Avatar name={user?.nome || user?.name || 'U'} size="sm" online />
        <div className="hidden sm:block min-w-0">
          <p className="text-label font-semibold text-text-primary leading-tight truncate max-w-[100px]">
            {user?.nome || user?.name || 'Utilizador'}
          </p>
          <p className="text-helper text-text-secondary" style={{ fontSize: '10px' }}>
            {user?.role === 'coordenador' ? 'Coordenador' : 'Aluno'}
          </p>
        </div>
      </div>
    </header>
  )
}
