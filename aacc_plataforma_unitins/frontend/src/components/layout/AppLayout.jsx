import { useState } from 'react'
import { cn } from '@/utils/cn'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

/**
 * Template raiz que combina Sidebar + Header + área de conteúdo.
 * Todos os layouts autenticados devem usar este componente.
 *
 * @param {React.ReactNode} children
 * @param {React.ReactNode} [breadcrumb]
 */
export function AppLayout({ children, breadcrumb }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-bg flex">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />

      {/* Conteúdo principal */}
      <div className={cn(
        'flex-1 flex flex-col min-w-0',
        'transition-[margin-left] duration-300',
        collapsed ? 'ml-16' : 'ml-sidebar',
      )}>
        <Header breadcrumb={breadcrumb} sidebarCollapsed={collapsed} />

        <main className="flex-1 mt-header p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
