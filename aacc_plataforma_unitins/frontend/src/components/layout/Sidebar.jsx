import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, FileText, BookOpen, Users,
  Settings, ChevronLeft, Search, GraduationCap, LogOut,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { Avatar } from '@/components/atoms/Avatar'

const NAV_ITEMS = [
  { label: 'Dashboard',    icon: LayoutDashboard, to: '/dashboard' },
  { label: 'Certificados', icon: FileText,         to: '/certificados' },
  { label: 'Categorias',   icon: BookOpen,         to: '/categorias' },
  { label: 'Alunos',       icon: Users,            to: '/alunos' },
]

const BOTTOM_ITEMS = [
  { label: 'Configurações', icon: Settings, to: '/configuracoes' },
]

/**
 * Sidebar principal da plataforma.
 * @param {boolean} collapsed - estado recolhido
 * @param {() => void} onToggle - callback para alternar
 */
export function Sidebar({ collapsed, onToggle }) {
  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen z-30',
        'bg-sidebar-bg border-r border-border',
        'flex flex-col transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-sidebar',
      )}
    >
      {/* ── Logo ────────────────────────────────────────────── */}
      <div className={cn(
        'flex items-center border-b border-border shrink-0',
        'h-header px-4 gap-3',
      )}>
        <div className="h-8 w-8 rounded-xs bg-primary flex items-center justify-center shrink-0">
          <GraduationCap className="h-5 w-5 text-text-inverse" />
        </div>
        {!collapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-label font-bold text-text-primary leading-tight truncate">
              AACC Platform
            </span>
            <span className="text-helper text-text-secondary truncate">UNITINS</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className={cn(
            'ml-auto rounded-xs p-1 text-text-secondary hover:bg-bg hover:text-text-primary',
            'transition-colors duration-normal',
            collapsed && 'mx-auto',
          )}
          aria-label={collapsed ? 'Expandir sidebar' : 'Recolher sidebar'}
        >
          <ChevronLeft className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* ── Pesquisa ─────────────────────────────────────────── */}
      {!collapsed && (
        <div className="px-3 py-3 border-b border-border shrink-0">
          <div className="flex items-center gap-2 px-3 h-8 rounded-xs border border-border bg-bg hover:border-border-strong cursor-pointer transition-colors">
            <Search className="h-3.5 w-3.5 text-text-secondary shrink-0" />
            <span className="text-helper text-text-disabled truncate">Pesquisar...</span>
            <span className="ml-auto text-[10px] text-text-disabled border border-border rounded px-1">⌘K</span>
          </div>
        </div>
      )}

      {/* ── Navegação ────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {!collapsed && (
          <p className="px-3 mb-1 text-helper text-text-disabled font-semibold uppercase tracking-wider">
            Menu
          </p>
        )}
        {NAV_ITEMS.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* ── Bottom ───────────────────────────────────────────── */}
      <div className="px-2 py-3 border-t border-border space-y-0.5 shrink-0">
        {BOTTOM_ITEMS.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}

        {/* Perfil */}
        <div className={cn(
          'flex items-center gap-3 px-3 py-2 rounded-xs cursor-pointer',
          'hover:bg-sidebar-hover transition-colors duration-normal mt-1',
          collapsed && 'justify-center',
        )}>
          <Avatar name="João Silva" size="sm" className="shrink-0" />
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="text-label font-medium text-text-primary truncate">João Silva</p>
              <p className="text-helper text-text-secondary truncate">aluno@unitins.br</p>
            </div>
          )}
          {!collapsed && (
            <LogOut className="h-4 w-4 text-text-secondary shrink-0 hover:text-danger transition-colors" />
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
      className={({ isActive }) =>
        cn('sidebar-item', isActive && 'active')
      }
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
          {!collapsed && (
            <span className="truncate">{item.label}</span>
          )}
        </>
      )}
    </NavLink>
  )
}
