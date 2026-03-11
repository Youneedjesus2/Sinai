import type { Metadata } from 'next'
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
        <header className="border-b">
          <div className="mx-auto max-w-7xl px-4 py-4">
            <h1 className="text-lg font-semibold tracking-tight">Sinai Lead Intake</h1>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  )
}
