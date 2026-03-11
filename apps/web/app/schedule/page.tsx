'use client'

import { useState } from 'react'
import Link from 'next/link'
import useSWR from 'swr'
import { getScheduledAppointments, swrKeys, type AppointmentWithLead, type AppointmentStatus } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toDateString(d: Date): string {
  return d.toISOString().split('T')[0]
}

function getMondayOf(d: Date): Date {
  const day = d.getDay()
  // getDay() returns 0=Sunday; treat Sunday as day 7 so Monday is always start
  const diff = day === 0 ? -6 : 1 - day
  const monday = new Date(d)
  monday.setDate(d.getDate() + diff)
  monday.setHours(0, 0, 0, 0)
  return monday
}

function addDays(d: Date, n: number): Date {
  const result = new Date(d)
  result.setDate(d.getDate() + n)
  return result
}

function formatDuration(start: string, end: string): string {
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const minutes = Math.round(ms / 60_000)
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}min` : `${h}h`
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const SHORT_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const STATUS_LABEL: Record<AppointmentStatus, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  cancelled: 'Cancelled',
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function SchedulePage() {
  const [weekStart, setWeekStart] = useState<Date>(() => getMondayOf(new Date()))

  const weekEnd = addDays(weekStart, 7)
  const startStr = toDateString(weekStart)
  const endStr = toDateString(weekEnd)

  const { data: appointments, isLoading } = useSWR<AppointmentWithLead[]>(
    swrKeys.scheduledAppointments(startStr, endStr),
    () => getScheduledAppointments(startStr, endStr),
    { refreshInterval: 60_000 }
  )

  // Build a map: date string → appointments
  const byDay = new Map<string, AppointmentWithLead[]>()
  for (let i = 0; i < 7; i++) {
    byDay.set(toDateString(addDays(weekStart, i)), [])
  }
  for (const appt of appointments ?? []) {
    if (!appt.start_time) continue
    const day = appt.start_time.split('T')[0]
    if (byDay.has(day)) {
      byDay.get(day)!.push(appt)
    }
  }

  const totalForWeek = appointments?.length ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Schedule</h2>
          <p className="text-sm text-muted-foreground">
            Week of {weekStart.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}
            {totalForWeek > 0 && ` · ${totalForWeek} consultation${totalForWeek !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setWeekStart((w) => addDays(w, -7))}>
            ← Prev
          </Button>
          <Button variant="outline" size="sm" onClick={() => setWeekStart(getMondayOf(new Date()))}>
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={() => setWeekStart((w) => addDays(w, 7))}>
            Next →
          </Button>
        </div>
      </div>

      {/* Calendar table */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                {Array.from({ length: 7 }).map((_, i) => {
                  const day = addDays(weekStart, i)
                  const isToday = toDateString(day) === toDateString(new Date())
                  return (
                    <th
                      key={i}
                      className={`px-3 py-3 text-left font-medium ${isToday ? 'text-primary' : 'text-muted-foreground'}`}
                    >
                      <span className="block">{SHORT_DAYS[i]}</span>
                      <span className={`text-xs ${isToday ? 'font-semibold text-primary' : 'font-normal'}`}>
                        {day.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              <tr className="align-top">
                {Array.from({ length: 7 }).map((_, i) => {
                  const dayKey = toDateString(addDays(weekStart, i))
                  const dayAppts = byDay.get(dayKey) ?? []
                  return (
                    <td key={i} className="border-r px-2 py-3 last:border-r-0 min-w-[120px]">
                      {dayAppts.length === 0 ? (
                        <p className="text-xs text-muted-foreground/50 text-center py-4">—</p>
                      ) : (
                        <div className="space-y-2">
                          {dayAppts.map((appt) => (
                            <Link
                              key={appt.id}
                              href={`/leads/${appt.lead_id}`}
                              className="block rounded-md border bg-background p-2 hover:bg-accent transition-colors"
                            >
                              <p className="font-medium leading-tight truncate">
                                {appt.lead_name ?? 'Unknown Lead'}
                              </p>
                              {appt.start_time && (
                                <p className="mt-0.5 text-xs text-muted-foreground">
                                  {formatTime(appt.start_time)}
                                  {appt.end_time && (
                                    <> · {formatDuration(appt.start_time, appt.end_time)}</>
                                  )}
                                </p>
                              )}
                              <div className="mt-1">
                                <Badge variant={appt.status as AppointmentStatus} className="text-[10px] px-1.5 py-0">
                                  {STATUS_LABEL[appt.status]}
                                </Badge>
                              </div>
                            </Link>
                          ))}
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && totalForWeek === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <p className="text-lg font-medium">No consultations scheduled.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Book a consultation from a lead&apos;s detail page.
          </p>
        </div>
      )}
    </div>
  )
}
