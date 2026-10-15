import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GraduationCap, BookOpen, Users, ArrowRight } from 'lucide-react'
import { AdminLayout } from '@/components/layout/AdminLayout'
import { StatsCard } from '@/components/organisms/StatsCard'
import { DashboardHero } from '@/components/organisms/DashboardHero'
import { cursosService, categoriasService, coordenadoresService } from '@/services/api/endpoints'

const contar = (res) => {
  const d = res.data
  return Array.isArray(d) ? d.length : (d.count ?? d.results?.length ?? 0)
}

const ATALHOS = [
  {
    to: '/admin/cursos',
    icon: GraduationCap,
    titulo: 'Cursos e Matrizes',
    descricao: 'Cadastre cursos e defina a carga horária de AACC de cada matriz curricular.',
  },
  {
    to: '/admin/categorias',
    icon: BookOpen,
    titulo: 'Eixos e Categorias',
    descricao: 'Gerencie os eixos formativos e as categorias de atividades da Resolução 057/2025.',
  },
  {
    to: '/admin/coordenadores',
    icon: Users,
    titulo: 'Coordenadores',
    descricao: 'Crie e acompanhe as contas dos coordenadores responsáveis pela auditoria.',
  },
]

export default function AdminDashboard() {
  const [totais, setTotais] = useState({ cursos: null, categorias: null, coordenadores: null })

  useEffect(() => {
    Promise.allSettled([
      cursosService.listar(),
      categoriasService.listar(),
      coordenadoresService.listar(),
    ]).then(([c, cat, coord]) => {
      setTotais({
        cursos:        c.status === 'fulfilled'     ? contar(c.value)     : null,
        categorias:    cat.status === 'fulfilled'   ? contar(cat.value)   : null,
        coordenadores: coord.status === 'fulfilled' ? contar(coord.value) : null,
      })
    })
  }, [])

  const fmt = (n) => (n == null ? '…' : String(n))

  return (
    <AdminLayout>
      <div className="space-y-8">
        <DashboardHero
          modulo="Administração Sistêmica • Parâmetros"
          titulo="Painel de Administração Sistêmica"
          descricao="Configure cursos, matrizes, categorias de atividades e coordenadores da plataforma AACC."
        />

        {/* Indicadores globais */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatsCard
            title="Cursos Cadastrados"
            value={fmt(totais.cursos)}
            icon={<GraduationCap className="h-5 w-5" />}
            color="primary"
            subtitle="Com matriz curricular de AACC"
          />
          <StatsCard
            title="Categorias Ativas"
            value={fmt(totais.categorias)}
            icon={<BookOpen className="h-5 w-5" />}
            color="warning"
            subtitle="Eixos e atividades da Res. 057/2025"
          />
          <StatsCard
            title="Coordenadores"
            value={fmt(totais.coordenadores)}
            icon={<Users className="h-5 w-5" />}
            color="success"
            subtitle="Contas com perfil de auditoria"
          />
        </div>

        {/* Atalhos rápidos */}
        <section className="surface rounded-xs overflow-hidden">
          <div className="px-6 py-4 border-b border-border bg-[#F8FAFC]">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-primary flex items-center">
              <span className="w-1 h-4 bg-gold mr-2 inline-block" />
              Atalhos Rápidos
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
            {ATALHOS.map(({ to, icon: Icon, titulo, descricao }) => (
              <Link
                key={to}
                to={to}
                className="group surface rounded-xs p-5 border-t-2 border-t-primary hover:border-t-gold hover:shadow-sm transition-colors flex flex-col gap-3"
              >
                <div className="h-11 w-11 rounded-xs bg-primary-light text-primary border border-primary-muted flex items-center justify-center">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-extrabold uppercase tracking-wider text-primary">{titulo}</p>
                  <p className="text-helper text-text-secondary mt-1">{descricao}</p>
                </div>
                <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-text-secondary group-hover:text-primary">
                  Acessar <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </AdminLayout>
  )
}
