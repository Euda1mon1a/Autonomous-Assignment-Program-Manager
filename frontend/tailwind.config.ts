import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/features/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      colors: {
        // Custom colors for schedule activities
        clinic: {
          light: '***REMOVED***dbeafe',
          DEFAULT: '***REMOVED***3b82f6',
          dark: '***REMOVED***1d4ed8',
        },
        inpatient: {
          light: '***REMOVED***ede9fe',
          DEFAULT: '***REMOVED***8b5cf6',
          dark: '***REMOVED***6d28d9',
        },
        call: {
          light: '***REMOVED***fee2e2',
          DEFAULT: '***REMOVED***ef4444',
          dark: '***REMOVED***b91c1c',
        },
        leave: {
          light: '***REMOVED***fef3c7',
          DEFAULT: '***REMOVED***f59e0b',
          dark: '***REMOVED***d97706',
        },
        // Tactical/Medical semantic colors
        scrub: {
          light: '***REMOVED***d1fae5',
          DEFAULT: '***REMOVED***10b981',
          dark: '***REMOVED***047857',
        },
        sterile: {
          light: '***REMOVED***f8fafc',
          DEFAULT: '***REMOVED***f1f5f9',
          dark: '***REMOVED***e2e8f0',
        },
      },
    },
  },
  plugins: [],
}
export default config
