import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FileText, BookOpen, Users,
  Settings, ChevronLeft, Search, GraduationCap, LogOut, ShieldCheck
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { Avatar } from '@/components/atoms/Avatar'
import { useAuth } from '@/contexts/AuthContext'

const NAV_ALUNO = [
  { label: 'Dashboard',    icon: LayoutDashboard, to: '/aluno/dashboard' },
  { label: 'Meus Certificados', icon: FileText, to: '/aluno/certificados' },
  { label: 'Enviar Novo',  icon: GraduationCap,   to: '/aluno/enviar' },
]

const NAV_COORDENADOR = [
  { label: 'Dashboard',    icon: LayoutDashboard, to: '/coordenador/dashboard' },
  { label: 'Fila de Revisão', icon: ShieldCheck, to: '/coordenador/revisao' },
  { label: 'Gestão de Alunos', icon: Users,      to: '/coordenador/alunos' },
  { label: 'Categorias AACC',  icon: BookOpen,   to: '/coordenador/categorias' },
]

const BOTTOM_ITEMS = [
  { label: 'Configurações', icon: Settings, to: '/configuracoes' },
]

export function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const navItems = user?.role === 'coordenador' ? NAV_COORDENADOR : NAV_ALUNO

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen z-30',
        'bg-sidebar-bg border-r border-border',
        'flex flex-col transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-sidebar',
      )}
    >
      {/* Logo */}
      <div className="flex items-center border-b border-border shrink-0 h-header px-4 gap-3">
        <div className="h-8 w-8 rounded-xs bg-primary flex items-center justify-center shrink-0">
          <GraduationCap className="h-5 w-5 text-text-inverse" />
        </div>
        {!collapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-label font-bold text-text-primary leading-tight truncate">
              AACC Platform
            </span>
            <span className="text-helper text-text-secondary truncate">
              {user?.role === 'coordenador' ? 'Coordenação' : 'Portal do Aluno'}
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            'ml-auto rounded-xs p-1 text-text-secondary hover:bg-bg hover:text-text-primary transition-colors',
            collapsed && 'mx-auto',
          )}
        >
          <ChevronLeft className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* Navegação */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5 mt-2">
        {!collapsed && (
          <p className="px-3 mb-1 text-helper text-text-disabled font-semibold uppercase tracking-wider">
            Menu
          </p>
        )}
        {navItems.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Bottom Profile */}
      <div className="px-2 py-3 border-t border-border space-y-0.5 shrink-0">
        {BOTTOM_ITEMS.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}

        <div 
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-xs cursor-pointer',
            'hover:bg-danger-light hover:text-danger transition-colors duration-normal mt-1 text-text-secondary group',
            collapsed && 'justify-center',
          )}
        >
          <Avatar name={user?.name} size="sm" className="shrink-0" />
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="text-label font-medium text-text-primary group-hover:text-danger truncate">
                {user?.name || 'Usuário'}
              </p>
              <p className="text-helper text-text-secondary group-hover:text-danger/80 truncate">
                {user?.email || 'email@unitins.br'}
              </p>
            </div>
          )}
          {!collapsed && (
            <LogOut className="h-4 w-4 shrink-0 transition-colors" />
          )}
        </div>
      </div>
    </aside>
  )
}

function SidebarLink({ item, collapsed }) {
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) => cn('sidebar-item', isActive && 'active')}
      title={collapsed ? item.label : undefined}
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'h-4 w-4 shrink-0 sidebar-icon transition-colors',
              isActive ? 'text-sidebar-iconActive' : 'text-sidebar-icon',
            )}
          />
          {!collapsed && <span className="truncate">{item.label}</span>}
        </>
      )}
    </NavLink>
  )
}
