import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, BookOpen, Users,
  Settings, PanelLeft, ShieldCheck, LogOut,
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
        'fixed left-0 top-0 h-screen z-30',
        'bg-slate-900 border-r border-slate-800 text-white',
        'flex flex-col transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* ── Logo ─────────────────────────────────────────────── */}
      <div className="flex items-center border-b border-slate-800 shrink-0 h-14 px-3 gap-2.5">
        <div className="h-7 w-7 rounded-xs bg-slate-700 flex items-center justify-center shrink-0">
          <ShieldCheck className="h-4 w-4 text-white" />
        </div>
        {!collapsed && (
          <div className="flex flex-col min-w-0 flex-1">
            <span className="text-sm font-bold leading-tight truncate text-white">
              AACC Platform
            </span>
            <span className="text-slate-400 truncate" style={{ fontSize: '10px' }}>
              Painel Sistêmico
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          title={collapsed ? 'Expandir menu' : 'Colapsar menu'}
          className={cn(
            'rounded-xs p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors',
            collapsed && 'mx-auto',
          )}
        >
          <PanelLeft className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* ── Navegação ────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {!collapsed && (
          <p className="px-2 mb-2 text-xs text-slate-500 font-semibold uppercase tracking-widest">
            Administração
          </p>
        )}
        {NAV_ADMIN.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) => cn(
              'flex items-center gap-3 px-3 py-2 rounded-xs transition-colors duration-200',
              isActive 
                ? 'bg-slate-800 text-white font-medium' 
                : 'text-slate-300 hover:bg-slate-800 hover:text-white',
              collapsed && 'justify-center'
            )}
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn('h-4 w-4 shrink-0', isActive ? 'text-white' : 'text-slate-400')} />
                {!collapsed && <span className="truncate text-sm">{item.label}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* ── Rodapé ───────────────────────────────────────────── */}
      <div className="px-2 py-2 border-t border-slate-800 shrink-0 space-y-0.5">
        <NavLink
          to="/configuracoes"
          title={collapsed ? 'Configurações' : undefined}
          className={({ isActive }) => cn(
            'flex items-center gap-3 px-3 py-2 rounded-xs transition-colors duration-200',
            isActive 
              ? 'bg-slate-800 text-white font-medium' 
              : 'text-slate-300 hover:bg-slate-800 hover:text-white',
            collapsed && 'justify-center'
          )}
        >
          {({ isActive }) => (
            <>
              <Settings className={cn('h-4 w-4 shrink-0', isActive ? 'text-white' : 'text-slate-400')} />
              {!collapsed && <span className="truncate text-sm">Configurações</span>}
            </>
          )}
        </NavLink>

        <button
          onClick={handleLogout}
          title="Sair"
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-xs',
            'text-slate-300 hover:bg-red-500/10 hover:text-red-400',
            'transition-colors duration-200 mt-1',
            collapsed && 'justify-center',
          )}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span className="truncate text-sm">Sair</span>}
        </button>
      </div>
    </aside>
  )
}

/**
 * Layout exclusivo para o Administrador, com Sidebar escura.
 */
export function AdminLayout({ children, title, breadcrumb }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 flex">
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

        <main className="flex-1 mt-14 bg-slate-50 p-6 sm:p-8 lg:p-10 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
