import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FileText, BookOpen, Users,
  Settings, PanelLeft, GraduationCap, LogOut,
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
        'fixed left-0 top-0 h-screen z-30',
        'bg-white border-r border-gray-200',
        'flex flex-col transition-[width] duration-300 ease-in-out',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* ── Logo ─────────────────────────────────────────────── */}
      <div className="flex items-center border-b border-border shrink-0 h-14 px-3 gap-2.5">
        <div className="h-7 w-7 rounded-xs bg-primary flex items-center justify-center shrink-0">
          <GraduationCap className="h-4 w-4 text-white" />
        </div>
        {!collapsed && (
          <div className="flex flex-col min-w-0 flex-1">
            <span className="text-label font-bold text-text-primary leading-tight truncate">
              AACC Platform
            </span>
            <span className="text-helper text-text-secondary truncate" style={{ fontSize: '10px' }}>
              {user?.role === 'coordenador' ? 'Coordenação' : 'Portal do Aluno'}
            </span>
          </div>
        )}
        <button
          onClick={onToggle}
          title={collapsed ? 'Expandir menu' : 'Colapsar menu'}
          className={cn(
            'rounded-xs p-1.5 text-text-secondary hover:bg-bg hover:text-text-primary transition-colors',
            collapsed && 'mx-auto',
          )}
        >
          <PanelLeft className={cn('h-4 w-4 transition-transform duration-300', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* ── Navegação ────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {!collapsed && (
          <p className="px-2 mb-2 text-helper text-text-disabled font-semibold uppercase tracking-widest">
            {user?.role === 'coordenador' ? 'Gestão' : 'Aluno'}
          </p>
        )}
        {navItems.map((item) => (
          <SidebarLink key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* ── Rodapé ───────────────────────────────────────────── */}
      <div className="px-2 py-2 border-t border-border shrink-0 space-y-0.5">
        <SidebarLink item={{ label: 'Configurações', icon: Settings, to: '/configuracoes' }} collapsed={collapsed} />

        <button
          onClick={handleLogout}
          title="Sair"
          className={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-xs',
            'text-text-secondary hover:bg-danger-light hover:text-danger',
            'transition-colors duration-normal group mt-1',
            collapsed && 'justify-center',
          )}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span className="truncate text-label">Sair</span>}
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
      className={({ isActive }) => cn('sidebar-item', isActive && 'active')}
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'h-4 w-4 shrink-0 sidebar-icon',
              isActive ? 'text-sidebar-iconActive' : 'text-sidebar-icon',
            )}
          />
          {!collapsed && <span className="truncate">{item.label}</span>}
        </>
      )}
    </NavLink>
  )
}
