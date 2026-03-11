'use client'

import { useRouter } from 'next/navigation'
import useSWR from 'swr'
import { getLeads, type Lead, type LeadStatus } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const AGENCY_ID = process.env.NEXT_PUBLIC_DEFAULT_AGENCY_ID ?? 'default'

const STATUS_LABEL: Record<LeadStatus, string> = {
  new: 'New',
  engaged: 'Engaged',
  qualified: 'Qualified',
  closed: 'Closed',
}

function LeadTableSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

export default function LeadsDashboard() {
  const router = useRouter()
  const { data: leads, error, isLoading } = useSWR<Lead[]>(
    `leads-${AGENCY_ID}`,
    () => getLeads(AGENCY_ID),
    { refreshInterval: 30_000 }
  )

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Leads</h2>
          <p className="text-sm text-muted-foreground">All inbound leads — refreshes every 30 seconds</p>
        </div>
        {leads && (
          <span className="text-sm text-muted-foreground">{leads.length} total</span>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load leads. Check that the API is running at{' '}
          <code className="font-mono">{process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}</code>.
        </div>
      )}

      {isLoading && <LeadTableSkeleton />}

      {!isLoading && !error && leads && leads.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <p className="text-lg font-medium">No leads yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Inbound leads from SMS, email, and web forms will appear here.
          </p>
        </div>
      )}

      {!isLoading && !error && leads && leads.length > 0 && (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Channel</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="cursor-pointer transition-colors hover:bg-muted/50"
                  onClick={() => router.push(`/leads/${lead.id}`)}
                >
                  <td className="px-4 py-3 font-medium">
                    {lead.name ?? <span className="text-muted-foreground italic">Unknown</span>}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground capitalize">{lead.source_channel}</td>
                  <td className="px-4 py-3">
                    <Badge variant={lead.status as LeadStatus}>
                      {STATUS_LABEL[lead.status]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(lead.created_at).toLocaleDateString()}
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
