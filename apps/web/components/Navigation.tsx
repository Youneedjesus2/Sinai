'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import useSWR from 'swr'
import { getLeads, getEscalatedLeads, swrKeys, type Lead } from '@/lib/api'
import { cn } from '@/lib/utils'

const AGENCY_ID = process.env.NEXT_PUBLIC_DEFAULT_AGENCY_ID ?? 'default'
const AGENCY_NAME = process.env.NEXT_PUBLIC_AGENCY_NAME ?? 'Sinai Lead Intake'

function NavBadge({
  count,
  variant = 'default',
}: {
  count: number
  variant?: 'default' | 'danger'
}) {
  if (count === 0) return null
  return (
    <span
      className={cn(
        'ml-auto rounded-full px-2 py-0.5 text-xs font-semibold',
        variant === 'danger'
          ? 'bg-red-100 text-red-700'
          : 'bg-muted text-muted-foreground'
      )}
    >
      {count}
    </span>
  )
}

export function Navigation() {
  const pathname = usePathname()

  const { data: leads } = useSWR<Lead[]>(
    swrKeys.leads(AGENCY_ID),
    () => getLeads(AGENCY_ID),
    { refreshInterval: 30_000 }
  )

  const { data: escalatedLeads } = useSWR<Lead[]>(
    swrKeys.escalations(AGENCY_ID),
    () => getEscalatedLeads(AGENCY_ID),
    { refreshInterval: 30_000 }
  )

  const newCount = leads?.filter((l) => l.status === 'new').length ?? 0
  const escalationCount = escalatedLeads?.length ?? 0

  const navItems = [
    { href: '/', label: 'Leads', badge: newCount, badgeVariant: 'default' as const },
    { href: '/schedule', label: 'Schedule', badge: 0, badgeVariant: 'default' as const },
    { href: '/escalations', label: 'Escalations', badge: escalationCount, badgeVariant: 'danger' as const },
  ]

  return (
    <nav className="flex h-full w-56 flex-col border-r bg-background px-3 py-6">
      <div className="mb-6 px-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {AGENCY_NAME}
        </p>
      </div>

      <ul className="space-y-1">
        {navItems.map((item) => {
          const isActive =
            item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                {item.label}
                <NavBadge count={item.badge} variant={item.badgeVariant} />
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
