'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { Summary } from '@/lib/api'

interface SummaryJson {
  escalation_reasons?: string[]
  unresolved_questions?: string[]
  next_steps?: string
  requested_service?: string
  care_needs?: string
  location?: string
  scheduled_time?: string
}

interface Props {
  leadId: number
  initialSummary: Summary | null | undefined
  onSummaryGenerated?: (summary: Summary) => void
}

export function SummaryPanel({ leadId, initialSummary, onSummaryGenerated }: Props) {
  const [summary, setSummary] = useState<Summary | null | undefined>(initialSummary)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const summaryJson = summary?.summary_json as SummaryJson | undefined

  async function handleGenerate() {
    setIsGenerating(true)
    setError(null)
    try {
      const res = await fetch('/api/generate-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ leadId }),
      })
      const data = (await res.json()) as Summary | { error?: string }
      if (!res.ok) {
        setError(('error' in data && data.error) ? data.error : `Error ${res.status}`)
        return
      }
      const newSummary = data as Summary
      setSummary(newSummary)
      onSummaryGenerated?.(newSummary)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate summary')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">AI Summary</CardTitle>
          <Button
            size="sm"
            variant="outline"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating…' : summary ? 'Regenerate' : 'Generate Summary'}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="text-sm space-y-3">
        {error && (
          <p className="text-destructive text-xs">{error}</p>
        )}

        {!summary && !isGenerating && (
          <p className="text-muted-foreground">No summary yet. Click &ldquo;Generate Summary&rdquo; to create one.</p>
        )}

        {isGenerating && (
          <p className="text-muted-foreground animate-pulse">Generating summary…</p>
        )}

        {summary && !isGenerating && (
          <>
            <p className="leading-relaxed">{summary.summary_text}</p>

            {summaryJson?.requested_service && (
              <div>
                <p className="font-medium text-muted-foreground mb-0.5">Requested Service</p>
                <p>{summaryJson.requested_service}</p>
              </div>
            )}

            {summaryJson?.care_needs && (
              <div>
                <p className="font-medium text-muted-foreground mb-0.5">Care Needs</p>
                <p>{summaryJson.care_needs}</p>
              </div>
            )}

            {summaryJson?.location && (
              <div>
                <p className="font-medium text-muted-foreground mb-0.5">Location</p>
                <p>{summaryJson.location}</p>
              </div>
            )}

            {summaryJson?.scheduled_time && (
              <div>
                <p className="font-medium text-muted-foreground mb-0.5">Scheduled Time</p>
                <p>{summaryJson.scheduled_time}</p>
              </div>
            )}

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
                <p className="font-medium text-muted-foreground mb-0.5">Next Steps</p>
                <p className="text-muted-foreground">{summaryJson.next_steps}</p>
              </div>
            )}

            <p className="text-xs text-muted-foreground border-t pt-2">
              Generated {new Date(summary.created_at).toLocaleString()}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
