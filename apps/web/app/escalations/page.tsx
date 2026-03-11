'use client'

import Link from 'next/link'
import useSWR from 'swr'
import { getEscalatedLeads, swrKeys, type Lead } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const AGENCY_ID = process.env.NEXT_PUBLIC_DEFAULT_AGENCY_ID ?? 'default'

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function EscalationsSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  )
}

export default function EscalationsPage() {
  const { data: leads, isLoading, error } = useSWR<Lead[]>(
    swrKeys.escalations(AGENCY_ID),
    () => getEscalatedLeads(AGENCY_ID),
    { refreshInterval: 30_000 }
  )

  // Sort by created_at descending (most recent first)
  const sorted = leads
    ? [...leads].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    : []

  const count = sorted.length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h2 className="text-2xl font-bold tracking-tight">
          Escalations{count > 0 ? ` (${count})` : ''}
        </h2>
        {count > 0 && (
          <Badge variant="escalated" className="text-sm">
            {count} need{count === 1 ? 's' : ''} attention
          </Badge>
        )}
      </div>
      <p className="text-sm text-muted-foreground">
        Leads whose conversation has been escalated to staff — refreshes every 30 seconds.
      </p>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load escalations.
        </div>
      )}

      {isLoading && <EscalationsSkeleton />}

      {!isLoading && !error && count === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <p className="text-lg font-medium">No escalations.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            All conversations are handled.
          </p>
        </div>
      )}

      {!isLoading && count > 0 && (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Lead</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Contact</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Channel</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {sorted.map((lead) => (
                <tr key={lead.id} className="transition-colors hover:bg-muted/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {lead.name ?? (
                          <span className="italic text-muted-foreground">Unknown</span>
                        )}
                      </span>
                      <Badge variant="escalated">Escalated</Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">Lead #{lead.id}</p>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {lead.email ? (
                      <span className="block truncate max-w-[180px]" title={lead.email}>
                        {lead.email}
                      </span>
                    ) : (
                      <span className="italic">No contact info</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground capitalize">
                    {lead.source_channel}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    <span title={new Date(lead.created_at).toLocaleString()}>
                      {timeAgo(lead.created_at)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/leads/${lead.id}`}
                      className="text-primary hover:underline font-medium"
                    >
                      View conversation →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
