import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, BookOpen, Users,
  Settings, PanelLeft, LogOut,
  ShieldCheck, SendHorizonal, History
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { useAuth } from '@/contexts/AuthContext'

const NAV_ALUNO = [
  { label: 'Dashboard',     icon: LayoutDashboard, to: '/aluno/dashboard' },
  { label: 'Enviar Novo',   icon: SendHorizonal,   to: '/aluno/enviar' },
  { label: 'Meu Histórico', icon: History,          to: '/aluno/historico' },
  { label: 'Manual de Categorias', icon: BookOpen, to: '/aluno/regras' },
]

const NAV_COORDENADOR = [
  { label: 'Dashboard',       icon: LayoutDashboard, to: '/coordenador/dashboard' },
  { label: 'Fila de Revisão', icon: ShieldCheck,     to: '/coordenador/revisao' },
  { label: 'Alunos',          icon: Users,            to: '/coordenador/alunos' },
  { label: 'Regras e Atividades', icon: BookOpen, to: '/coordenador/regras' },
]

export function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const navItems = user?.role === 'coordenador' ? NAV_COORDENADOR : NAV_ALUNO
  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen z-30 text-white',
        'bg-sidebar-bg border-r border-sidebar-border',
        'flex flex-col transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* ── Marca Unitins ────────────────────────────────────── */}
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
            <span className="text-[10px] font-semibold tracking-widest text-gold uppercase mt-1 truncate">
              Portal AACC
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
            {user?.role === 'coordenador' ? 'Menu' : 'Navegação'}
          </p>
        )}
        {navItems.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* ── Rodapé ───────────────────────────────────────────── */}
      <div className="px-2 py-2 border-t border-sidebar-border shrink-0 space-y-0.5">
        <SidebarLink item={{ label: 'Configurações', icon: Settings, to: '/configuracoes' }} collapsed={collapsed} />

        <button
          onClick={handleLogout}
          title="Sair"
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-xs',
            'text-gray-300 hover:bg-danger-light hover:text-danger',
            'uppercase tracking-wider text-xs font-semibold',
            'transition-colors duration-normal group mt-1',
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

function SidebarLink({ item, collapsed }) {
  return (
    <NavLink
      to={item.to}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) => cn('sidebar-item', isActive && 'active', collapsed && 'justify-center')}
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'h-4 w-4 shrink-0 sidebar-icon',
              isActive ? 'text-gold' : 'text-primary-muted',
            )}
          />
          {!collapsed && <span className="truncate">{item.label}</span>}
        </>
      )}
    </NavLink>
  )
}
