import type { Metadata } from 'next'
import { Navigation } from '@/components/Navigation'
import './globals.css'

export const metadata: Metadata = {
  title: 'Sinai — Lead Intake Dashboard',
  description: 'Staff-facing dashboard for the Healthcare AI Lead Intake Agent',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        <div className="flex min-h-screen">
          <Navigation />
          <main className="flex-1 overflow-y-auto px-6 py-6">{children}</main>
        </div>
      </body>
    </html>
  )
}
