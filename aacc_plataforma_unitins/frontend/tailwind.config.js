/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0B5ED7',
          hover:   '#094DB1',
          light:   '#EFF6FF',
          muted:   '#BFDBFE',
        },
        secondary: {
          DEFAULT: '#0A2F6B',
        },
        success: {
          DEFAULT: '#16A34A',
          light:   '#F0FDF4',
          muted:   '#BBF7D0',
        },
        warning: {
          DEFAULT: '#EAB308',
          light:   '#FEFCE8',
          muted:   '#FDE68A',
        },
        danger: {
          DEFAULT: '#DC2626',
          light:   '#FEF2F2',
          muted:   '#FECACA',
        },
        bg: {
          DEFAULT: '#F7F9FC',
          surface: '#FFFFFF',
        },
        border: {
          DEFAULT: '#E5E7EB',
          strong:  '#D1D5DB',
        },
        text: {
          primary:   '#1D2939',
          secondary: '#667085',
          disabled:  '#9CA3AF',
          inverse:   '#FFFFFF',
        },
        sidebar: {
          bg:          '#FFFFFF',
          active:      '#EFF6FF',
          activeBorder:'#0B5ED7',
          hover:       '#F7F9FC',
          text:        '#667085',
          textActive:  '#0B5ED7',
          icon:        '#9CA3AF',
          iconActive:  '#0B5ED7',
        },
      },
      spacing: {
        1:  '4px',
        2:  '8px',
        3:  '12px',
        4:  '16px',
        5:  '20px',
        6:  '24px',
        8:  '32px',
        10: '40px',
        12: '48px',
        16: '64px',
        20: '80px',
        24: '96px',
      },
      borderRadius: {
        xs: '8px',
        sm: '12px',
        md: '16px',
        lg: '20px',
        xl: '24px',
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgba(16, 24, 40, 0.05)',
        sm: '0 1px 3px 0 rgba(16, 24, 40, 0.08), 0 1px 2px -1px rgba(16, 24, 40, 0.04)',
        md: '0 4px 8px -2px rgba(16, 24, 40, 0.08), 0 2px 4px -2px rgba(16, 24, 40, 0.04)',
        lg: '0 12px 16px -4px rgba(16, 24, 40, 0.08), 0 4px 6px -2px rgba(16, 24, 40, 0.04)',
        xl: '0 20px 24px -4px rgba(16, 24, 40, 0.08), 0 8px 8px -4px rgba(16, 24, 40, 0.04)',
      },
      fontFamily: {
        sans: ['Inter', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        display: ['40px', { lineHeight: '48px', fontWeight: '700' }],
        h1:      ['32px', { lineHeight: '40px', fontWeight: '700' }],
        h2:      ['28px', { lineHeight: '36px', fontWeight: '600' }],
        h3:      ['24px', { lineHeight: '32px', fontWeight: '600' }],
        card:    ['18px', { lineHeight: '28px', fontWeight: '600' }],
        body:    ['16px', { lineHeight: '24px', fontWeight: '400' }],
        label:   ['14px', { lineHeight: '20px', fontWeight: '500' }],
        helper:  ['13px', { lineHeight: '20px', fontWeight: '400' }],
      },
      screens: {
        '2xl': '1440px',
        xl:    '1280px',
        lg:    '1024px',
        md:    '768px',
        sm:    '480px',
      },
      transitionDuration: {
        fast:   '100ms',
        normal: '200ms',
        slow:   '300ms',
      },
      width: {
        sidebar:         '260px',
        'sidebar-collapsed': '64px',
      },
      height: {
        header: '72px',
      },
      animation: {
        'fade-in':    'fadeIn 200ms ease-out',
        'slide-in':   'slideIn 200ms ease-out',
        'scale-in':   'scaleIn 150ms ease-out',
        'spin-slow':  'spin 2s linear infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' },                    to: { opacity: '1' } },
        slideIn: { from: { transform: 'translateY(-8px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
        scaleIn: { from: { transform: 'scale(0.96)', opacity: '0' },       to: { transform: 'scale(1)', opacity: '1' } },
      },
    },
  },
  plugins: [],
}
