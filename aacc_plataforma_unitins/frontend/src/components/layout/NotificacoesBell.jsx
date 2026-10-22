/**
 * NotificacoesBell.jsx — UC04.3
 * Sino com badge de não lidas (polling a cada 30s) + dropdown de mensagens.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { Bell, Check, CheckCheck } from 'lucide-react'
import { notificacaoService } from '@/services/api/endpoints'
import { cn } from '@/utils/cn'

const POLL_MS = 30000

function tempoRelativo(iso) {
  const diff = Math.max(0, Date.now() - new Date(iso).getTime())
  const min = Math.floor(diff / 60000)
  if (min < 1) return 'agora'
  if (min < 60) return `há ${min} min`
  const h = Math.floor(min / 60)
  if (h < 24) return `há ${h} h`
  return new Date(iso).toLocaleDateString('pt-BR')
}

export function NotificacoesBell() {
  const [itens, setItens] = useState([])
  const [aberto, setAberto] = useState(false)
  const ref = useRef(null)

  const carregar = useCallback(async () => {
    try {
      const { data } = await notificacaoService.listar({ lida: false })
      setItens(Array.isArray(data) ? data : (data.results ?? []))
    } catch {
      /* silencioso: polling não deve incomodar o usuário */
    }
  }, [])

  useEffect(() => {
    carregar()
    const t = setInterval(carregar, POLL_MS)
    return () => clearInterval(t)
  }, [carregar])

  useEffect(() => {
    if (!aberto) return
    const fora = (e) => { if (ref.current && !ref.current.contains(e.target)) setAberto(false) }
    document.addEventListener('mousedown', fora)
    return () => document.removeEventListener('mousedown', fora)
  }, [aberto])

  const marcarLida = async (id) => {
    setItens(prev => prev.filter(n => n.id !== id)) // remove o aviso visual de imediato
    try { await notificacaoService.marcarLida(id) } catch { carregar() }
  }

  const marcarTodas = async () => {
    setItens([])
    try { await notificacaoService.marcarTodasLidas() } catch { carregar() }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => { setAberto(o => !o); if (!aberto) carregar() }}
        aria-label={`Notificações${itens.length ? ` (${itens.length} não lidas)` : ''}`}
        className="relative h-9 w-9 flex items-center justify-center rounded-xs text-primary hover:bg-primary-light transition-colors"
      >
        <Bell className="h-5 w-5 text-primary" />
        {itens.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-danger text-white text-[10px] font-bold flex items-center justify-center">
            {itens.length > 9 ? '9+' : itens.length}
          </span>
        )}
      </button>

      {aberto && (
        <div className="absolute right-0 mt-2 w-80 max-w-[90vw] surface z-50 overflow-hidden">
          <div className="flex items-center justify-between bg-primary text-white text-xs uppercase tracking-wider px-4 py-2.5">
            <p className="font-semibold text-white">Notificações</p>
            {itens.length > 0 && (
              <button type="button" onClick={marcarTodas}
                className="flex items-center gap-1 text-[11px] text-white/90 hover:text-white hover:underline">
                <CheckCheck className="h-3.5 w-3.5" /> Marcar todas
              </button>
            )}
          </div>

          {itens.length === 0 ? (
            <p className="px-4 py-8 text-center text-helper text-gray-500">Nenhuma notificação nova.</p>
          ) : (
            <ul className="max-h-80 overflow-y-auto divide-y divide-gray-100">
              {itens.map(n => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => marcarLida(n.id)}
                    className={cn('w-full text-left px-4 py-3 flex gap-3 items-start hover:bg-gray-50 transition-colors')}
                  >
                    <span className="mt-1.5 h-2 w-2 rounded-full bg-red-600 shrink-0" />
                    <span className="flex-1 min-w-0">
                      <span className="block text-helper text-gray-800 leading-snug break-words">{n.mensagem}</span>
                      <span className="block text-[10px] text-gray-400 mt-1">{tempoRelativo(n.criado_em)}</span>
                    </span>
                    <Check className="h-4 w-4 text-gray-400 shrink-0 mt-0.5" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
