import { Inter, JetBrains_Mono } from 'next/font/google'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from '@/components/Navigation'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { KeyboardShortcutHelp } from '@/components/common/KeyboardShortcutHelp'
import { CommandPalette } from '@/components/CommandPalette'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'Residency Scheduler',
  description: 'Medical residency scheduling with ACGME compliance',
  robots: 'noindex, nofollow', // Private app
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f8fafc' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`h-full ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="h-full font-sans antialiased overflow-x-hidden">
        <Providers>
          <ErrorBoundary>
            <div className="flex flex-col min-h-screen">
              <Navigation />
              <main className="flex-1 w-full">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
                  {children}
                </div>
              </main>
            </div>
            <KeyboardShortcutHelp />
            <CommandPalette />
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  )
}
