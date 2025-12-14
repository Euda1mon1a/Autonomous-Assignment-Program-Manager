import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from '@/components/Navigation'
import { ErrorBoundary } from '@/components/ErrorBoundary'

export const metadata: Metadata = {
  title: 'Residency Scheduler',
  description: 'ACGME-compliant residency program scheduling',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <ErrorBoundary>
            <div className="min-h-screen bg-gray-50">
              <Navigation />
              <main>{children}</main>
            </div>
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  )
}
