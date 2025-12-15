import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/features/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
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
      },
    },
  },
  plugins: [],
}
export default config
