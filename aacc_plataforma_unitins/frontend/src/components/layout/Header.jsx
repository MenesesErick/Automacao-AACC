import { Bell, Search } from 'lucide-react'
import { cn } from '@/utils/cn'
import { Avatar } from '@/components/atoms/Avatar'
import { useAuth } from '@/contexts/AuthContext'

export function Header({ breadcrumb, sidebarCollapsed }) {
  const { user } = useAuth()

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-20 flex items-center gap-4 px-6',
        'h-header bg-bg-surface border-b border-border',
        'transition-[left] duration-300',
        sidebarCollapsed ? 'left-16' : 'left-sidebar',
      )}
    >
      <div className="flex-1 min-w-0">
        {breadcrumb ?? <p className="text-label text-text-secondary truncate">AACC Platform</p>}
      </div>

      <div className="hidden md:flex items-center gap-2 h-8 px-3 rounded-xs border border-border bg-bg hover:border-border-strong cursor-pointer transition-colors w-52">
        <Search className="h-3.5 w-3.5 text-text-secondary shrink-0" />
        <span className="text-helper text-text-disabled">Pesquisa global...</span>
      </div>

      <button className="relative p-2 rounded-xs text-text-secondary hover:text-text-primary hover:bg-bg transition-colors">
        <Bell className="h-5 w-5" />
        <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-danger border-2 border-bg-surface" />
      </button>

      <Avatar name={user?.name || 'Usuário'} size="sm" online />
    </header>
  )
}
