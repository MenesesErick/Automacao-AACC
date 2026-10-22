/** Utilitário para mesclar classNames com suporte a Tailwind conflicts. */
import { clsx } from 'clsx'
import { extendTailwindMerge } from 'tailwind-merge'

const customTwMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      'font-size': [
        'text-display',
        'text-h1',
        'text-h2',
        'text-h3',
        'text-card',
        'text-body',
        'text-label',
        'text-helper',
      ],
    },
  },
})

/**
 * @param {...import('clsx').ClassValue} inputs
 * @returns {string}
 */
export function cn(...inputs) {
  return customTwMerge(clsx(inputs))
}
