import { cn } from '@/utils/cn'
import { Avatar } from '@/components/atoms/Avatar'
import { useAuth } from '@/contexts/AuthContext'

export function Header({ title, breadcrumb, sidebarCollapsed }) {
  const { user } = useAuth()

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-20 flex items-center justify-between gap-4 px-4 sm:px-6',
        'h-14 bg-white border-b border-gray-200',
        'transition-[left] duration-300',
        sidebarCollapsed ? 'left-16' : 'left-60',
      )}
    >
      {/* Título da página (esquerda) */}
      <div className="min-w-0 flex items-center">
        {title ? (
          <h1 className="text-xl font-semibold text-gray-800 truncate">{title}</h1>
        ) : (
          breadcrumb ?? (
            <h1 className="text-xl font-semibold text-gray-800 truncate">AACC Platform</h1>
          )
        )}
      </div>

      {/* Perfil (direita) */}
      <div className="flex items-center gap-2 shrink-0">
        <Avatar name={user?.nome || user?.name || 'U'} size="sm" online />
        <div className="hidden sm:block min-w-0">
          <p className="text-label font-semibold text-gray-800 leading-tight truncate max-w-[140px]">
            {user?.nome || user?.name || 'Utilizador'}
          </p>
          <p className="text-gray-500" style={{ fontSize: '10px' }}>
            {user?.role === 'coordenador' ? 'Coordenador' : 'Aluno'}
          </p>
        </div>
      </div>
    </header>
  )
}
