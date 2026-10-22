import { cn } from '@/utils/cn'

/**
 * Tabela de dados genérica e reutilizável.
 *
 * @param {Array<{key: string, label: string, render?: (row) => React.ReactNode}>} columns
 * @param {Array<Object>} data
 * @param {string} [emptyLabel='Nenhum registro encontrado.']
 * @param {boolean} [loading=false]
 * @param {(row: Object) => void} [onRowClick]
 */
export function DataTable({
  columns = [],
  data    = [],
  emptyLabel = 'Nenhum registro encontrado.',
  loading = false,
  onRowClick,
  className,
}) {
  return (
    <div className={cn('overflow-hidden rounded-xs border border-border bg-white', className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          {/* Cabeçalho */}
          <thead>
            <tr className="border-b-2 border-primary/20 bg-primary-light text-primary">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-left text-[11px] font-extrabold uppercase tracking-wider whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>

          {/* Corpo */}
          <tbody className="divide-y divide-border">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="even:bg-gray-50/50">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      <div className="h-4 w-24 animate-pulse rounded-xs bg-bg" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-10 text-center text-xs uppercase tracking-wider text-text-secondary"
                >
                  {emptyLabel}
                </td>
              </tr>
            ) : (
              data.map((row, rowIdx) => (
                <tr
                  key={row.id ?? rowIdx}
                  onClick={() => onRowClick?.(row)}
                  className={cn(
                    'even:bg-gray-50/50 hover:bg-primary-light/40 transition-colors',
                    onRowClick && 'cursor-pointer group',
                  )}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-sm text-text-primary">
                      {col.render ? col.render(row) : row[col.key] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
