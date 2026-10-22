import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, BookOpen, Users,
  Settings, PanelLeft, LogOut,
  GraduationCap
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { Header } from './Header'
import { useAuth } from '@/contexts/AuthContext'

const NAV_ADMIN = [
  { label: 'Dashboard',          icon: LayoutDashboard, to: '/admin/dashboard' },
  { label: 'Cursos e Matrizes',  icon: GraduationCap,   to: '/admin/cursos' },
  { label: 'Eixos e Categorias', icon: BookOpen,        to: '/admin/categorias' },
  { label: 'Coordenadores',      icon: Users,           to: '/admin/coordenadores' },
]

function AdminSidebar({ collapsed, onToggle }) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen z-30 text-white',
        'bg-[#051324] border-r border-sidebar-border',
        'flex flex-col transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* ── Marca Unitins Admin ──────────────────────────────── */}
      <div
        className={cn(
          'shrink-0 border-b border-sidebar-border bg-[#06182C]',
          collapsed
            ? 'flex flex-col items-center justify-center px-2 py-3 gap-2'
            : 'h-16 px-4 flex items-center gap-3',
        )}
      >
        <div className="h-9 w-9 rounded-sm border border-gold/60 bg-primary text-gold font-extrabold flex items-center justify-center shrink-0 text-sm">
          U
        </div>
        {!collapsed && (
          <div className="flex flex-col min-w-0 flex-1">
            <span className="font-extrabold tracking-widest text-white text-base leading-none truncate">
              UNITINS
            </span>
            <span className="text-gold uppercase tracking-widest text-[10px] font-semibold mt-1 truncate">
              Administração Sistêmica
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          title={collapsed ? 'Expandir menu' : 'Colapsar menu'}
          className={cn(
            'rounded-xs p-1.5 text-primary-muted hover:bg-sidebar-hover hover:text-white transition-colors',
            collapsed && 'mx-auto flex items-center justify-center w-8 h-8',
          )}
        >
          <PanelLeft className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* ── Navegação ────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {!collapsed && (
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary-muted/70 px-3 mb-2">
            Menu
          </p>
        )}
        {NAV_ADMIN.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) => cn(
              'flex items-center gap-3 px-3 py-2 rounded-xs',
              'uppercase tracking-wider text-xs font-semibold',
              'transition-colors duration-normal',
              isActive
                ? 'bg-sidebar-active text-white border-l-4 border-gold pl-2'
                : 'text-gray-300 hover:bg-sidebar-hover hover:text-white',
              collapsed && 'justify-center',
            )}
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={cn(
                    'h-4 w-4 shrink-0',
                    isActive ? 'text-gold' : 'text-primary-muted',
                  )}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* ── Rodapé ───────────────────────────────────────────── */}
      <div className="px-2 py-2 border-t border-sidebar-border shrink-0 space-y-0.5">
        <NavLink
          to="/configuracoes"
          title={collapsed ? 'Configurações' : undefined}
          className={({ isActive }) => cn(
            'flex items-center gap-3 px-3 py-2 rounded-xs',
            'uppercase tracking-wider text-xs font-semibold',
            'transition-colors duration-normal',
            isActive
              ? 'bg-sidebar-active text-white border-l-4 border-gold pl-2'
              : 'text-gray-300 hover:bg-sidebar-hover hover:text-white',
            collapsed && 'justify-center',
          )}
        >
          {({ isActive }) => (
            <>
              <Settings
                className={cn(
                  'h-4 w-4 shrink-0',
                  isActive ? 'text-gold' : 'text-primary-muted',
                )}
              />
              {!collapsed && <span className="truncate">Configurações</span>}
            </>
          )}
        </NavLink>

        <button
          onClick={handleLogout}
          title="Sair"
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-xs',
            'text-gray-300 hover:bg-danger-light hover:text-danger',
            'uppercase tracking-wider text-xs font-semibold',
            'transition-colors duration-normal mt-1 group',
            collapsed && 'justify-center',
          )}
        >
          <LogOut className="h-4 w-4 shrink-0 text-primary-muted group-hover:text-danger" />
          {!collapsed && <span className="truncate">Sair</span>}
        </button>
      </div>
    </aside>
  )
}

/**
 * Layout exclusivo para o Administrador, com Sidebar institucional sóbria.
 */
export function AdminLayout({ children, title, breadcrumb }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-bg flex">
      <AdminSidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />

      {/* Área principal */}
      <div
        className={cn(
          'flex-1 flex flex-col min-w-0 min-h-screen',
          'transition-[margin-left] duration-300',
          collapsed ? 'ml-16' : 'ml-60',
        )}
      >
        <Header
          title={title}
          breadcrumb={breadcrumb || 'Painel de Administração Sistêmica'}
          sidebarCollapsed={collapsed}
        />

        <main className="flex-1 mt-16 bg-bg p-6 sm:p-8 lg:p-10 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
