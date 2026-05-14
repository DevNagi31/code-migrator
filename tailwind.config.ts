import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'SF Pro Text',
          'Inter', 'Helvetica Neue', 'sans-serif',
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      colors: {
        ink: { 50: '#f5f5f7', 100: '#e5e5e7', 200: '#c7c7cc',
               400: '#86868b', 600: '#424245', 800: '#1d1d1f', 900: '#000' },
        accent: { DEFAULT: '#0071e3', hover: '#0077ED' },
        success: '#0a7c2f', warn: '#b07b00', danger: '#a8322a',
      },
      letterSpacing: { tightest: '-0.022em' },
      boxShadow: {
        soft: '0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)',
        glass: '0 1px 0 rgba(255,255,255,0.6) inset, 0 8px 30px rgba(0,0,0,0.06)',
      },
    },
  },
  plugins: [],
};

export default config;
