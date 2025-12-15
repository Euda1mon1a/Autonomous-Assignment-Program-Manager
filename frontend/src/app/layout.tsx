import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from '@/components/Navigation'
import { ErrorBoundary } from '@/components/ErrorBoundary'

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
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
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
      <body className="h-full font-sans antialiased overflow-x-hidden">
        <Providers>
          <ErrorBoundary>
            <div className="flex flex-col min-h-screen bg-gray-50">
              <Navigation />
              <main className="flex-1 w-full">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
                  {children}
                </div>
              </main>
            </div>
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  )
}
