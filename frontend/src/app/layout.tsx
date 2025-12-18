import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from '@/components/Navigation'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { KeyboardShortcutHelp } from '@/components/common/KeyboardShortcutHelp'

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
    <html lang="en" className="h-full">
      <head>
        {/* Load Inter + JetBrains Mono from Google Fonts CDN for production */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
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
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  )
}
