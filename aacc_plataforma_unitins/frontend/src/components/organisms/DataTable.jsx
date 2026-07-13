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
    <div className={cn('surface rounded-sm overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          {/* Cabeçalho */}
          <thead>
            <tr className="border-b border-border bg-bg">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-helper font-semibold text-text-secondary uppercase tracking-wider whitespace-nowrap"
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
                <tr key={i}>
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      <div className="h-4 bg-bg rounded-xs animate-pulse w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-label text-text-secondary"
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
                    'transition-colors duration-fast',
                    onRowClick && 'cursor-pointer hover:bg-bg',
                  )}
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3 text-label text-text-primary">
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
