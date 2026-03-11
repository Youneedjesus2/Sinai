'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import useSWR from 'swr'
import {
  getLead,
  getLeadConversations,
  getLeadAppointments,
  getLeadSummary,
  generateLeadSummary,
  swrKeys,
  type ConversationState,
  type Summary,
} from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EscalationBanner } from './components/EscalationBanner'

const STATE_LABEL: Record<ConversationState, string> = {
  intake: 'Intake',
  awaiting_follow_up: 'Awaiting Follow-Up',
  escalated: 'Escalated',
  completed: 'Completed',
}

export default function LeadDetailPage() {
  const params = useParams()
  const router = useRouter()
  const leadId = Number(params.id)

  const [isGenerating, setIsGenerating] = useState(false)
  const [generateError, setGenerateError] = useState<string | null>(null)

  const { data: lead, isLoading: leadLoading } = useSWR(
    swrKeys.lead(leadId),
    () => getLead(leadId)
  )

  const { data: conversations, isLoading: convsLoading } = useSWR(
    swrKeys.conversations(leadId),
    () => getLeadConversations(leadId),
    { refreshInterval: 15_000 }
  )

  const { data: appointments } = useSWR(
    swrKeys.appointments(leadId),
    () => getLeadAppointments(leadId)
  )

  const { data: summary, mutate: mutateSummary } = useSWR(
    swrKeys.summary(leadId),
    () => getLeadSummary(leadId).catch((err: Error) => {
      // 404 is expected when no summary yet — return null
      if (err.message.includes('404')) return null
      throw err
    })
  )

  const latestConversation = conversations?.[0]
  const isEscalated = latestConversation?.current_state === 'escalated'

  const summaryJson = summary?.summary_json as {
    escalation_reasons?: string[]
    unresolved_questions?: string[]
    next_steps?: string
    requested_service?: string
    care_needs?: string
    location?: string
    scheduled_time?: string
  } | undefined

  async function handleGenerateSummary() {
    setIsGenerating(true)
    setGenerateError(null)
    try {
      const newSummary = await generateLeadSummary(leadId)
      await mutateSummary(newSummary as Summary)
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Failed to generate summary')
    } finally {
      setIsGenerating(false)
    }
  }

  if (leadLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="text-center py-16">
        <p className="text-muted-foreground">Lead not found.</p>
        <Button variant="link" onClick={() => router.push('/')}>Back to dashboard</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => router.push('/')}
            className="mb-2 text-sm text-muted-foreground hover:text-foreground"
          >
            ← All leads
          </button>
          <h2 className="text-2xl font-bold">
            {lead.name ?? <span className="text-muted-foreground italic">Unknown Lead</span>}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground capitalize">
            {lead.source_channel} &middot; Lead #{lead.id}
          </p>
        </div>
        <Badge variant={lead.status}>{lead.status}</Badge>
      </div>

      {/* Escalation banner */}
      {isEscalated && (
        <EscalationBanner reasons={summaryJson?.escalation_reasons ?? []} />
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Conversation timeline (2/3 width) */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-semibold">Conversation</h3>

          {convsLoading && (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          )}

          {!convsLoading && (!conversations || conversations.length === 0) && (
            <p className="text-sm text-muted-foreground">No conversation history yet.</p>
          )}

          {conversations?.map((conv) => (
            <div key={conv.id} className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant={conv.current_state as ConversationState}>
                  {STATE_LABEL[conv.current_state]}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  Last active {new Date(conv.last_message_at).toLocaleString()}
                </span>
              </div>

              <div className="space-y-2 pl-2">
                {conv.messages?.map((msg) => (
                  <div
                    key={msg.id}
                    className={`rounded-lg px-4 py-2 text-sm max-w-[85%] ${
                      msg.direction === 'inbound'
                        ? 'bg-muted'
                        : 'ml-auto bg-primary text-primary-foreground'
                    }`}
                  >
                    <p className="text-xs font-medium mb-1 opacity-70 capitalize">
                      {msg.direction} &middot; {msg.channel}
                    </p>
                    <p>{msg.body}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Right panel (1/3 width) */}
        <div className="space-y-4">
          {/* Lead info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Lead Info</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Status</span>
                <Badge variant={lead.status}>{lead.status}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Channel</span>
                <span className="capitalize">{lead.source_channel}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created</span>
                <span>{new Date(lead.created_at).toLocaleDateString()}</span>
              </div>
              {latestConversation && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">State</span>
                  <Badge variant={latestConversation.current_state as ConversationState}>
                    {STATE_LABEL[latestConversation.current_state]}
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Appointments */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Appointments</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              {!appointments || appointments.length === 0 ? (
                <p className="text-muted-foreground">No appointments scheduled.</p>
              ) : (
                <div className="space-y-2">
                  {appointments.map((appt) => (
                    <div key={appt.id} className="rounded-md border p-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium capitalize">{appt.status}</span>
                        <Badge variant={appt.status as 'pending' | 'confirmed' | 'cancelled'}>
                          {appt.status}
                        </Badge>
                      </div>
                      {appt.start_time && (
                        <p className="mt-1 text-muted-foreground">
                          {new Date(appt.start_time).toLocaleString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Summary */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">AI Summary</CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleGenerateSummary}
                  disabled={isGenerating}
                >
                  {isGenerating ? 'Generating…' : summary ? 'Regenerate' : 'Generate'}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="text-sm space-y-3">
              {generateError && (
                <p className="text-destructive text-xs">{generateError}</p>
              )}

              {!summary && !isGenerating && (
                <p className="text-muted-foreground">No summary yet.</p>
              )}

              {summary && (
                <>
                  <p className="leading-relaxed">{summary.summary_text}</p>

                  {summaryJson?.unresolved_questions && summaryJson.unresolved_questions.length > 0 && (
                    <div>
                      <p className="font-medium text-muted-foreground mb-1">Unresolved Questions</p>
                      <ul className="list-inside list-disc space-y-1 text-muted-foreground">
                        {summaryJson.unresolved_questions.map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {summaryJson?.next_steps && (
                    <div>
                      <p className="font-medium text-muted-foreground mb-1">Next Steps</p>
                      <p className="text-muted-foreground">{summaryJson.next_steps}</p>
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground">
                    Generated {new Date(summary.created_at).toLocaleString()}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
