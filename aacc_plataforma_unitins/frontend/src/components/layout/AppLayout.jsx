import { useState } from 'react'
import { cn } from '@/utils/cn'
import { Sidebar } from './Sidebar'
import { Header } from './Header'

/**
 * Template raiz que combina Sidebar + Header + área de conteúdo.
 * Todos os layouts autenticados devem usar este componente.
 */
export function AppLayout({ children, title, breadcrumb }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-bg flex">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />

      {/* Área principal */}
      <div
        className={cn(
          'flex-1 flex flex-col min-w-0 min-h-screen',
          'transition-[margin-left] duration-300',
          collapsed ? 'ml-16' : 'ml-60',
        )}
      >
        <Header title={title} breadcrumb={breadcrumb} sidebarCollapsed={collapsed} />

        <main className="flex-1 mt-16 bg-bg p-6 sm:p-8 lg:p-10 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
