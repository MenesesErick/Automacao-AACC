import { ShieldCheck } from 'lucide-react'
import { AdminLayout } from '@/components/layout/AdminLayout'

export default function AdminDashboard() {
  return (
    <AdminLayout>
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
          <ShieldCheck className="h-8 w-8 text-slate-800" />
        </div>
        <h2 className="text-2xl font-semibold text-slate-900 mb-2">Painel de Administração Sistêmica</h2>
        <p className="text-slate-500 max-w-md">
          Bem-vindo à área administrativa. Utilize o menu lateral para gerenciar cursos, categorias e coordenadores.
        </p>
      </div>
    </AdminLayout>
  )
}
