const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type LeadStatus = 'new' | 'engaged' | 'qualified' | 'closed'
export type ConversationState = 'intake' | 'awaiting_follow_up' | 'escalated' | 'completed'
export type MessageDirection = 'inbound' | 'outbound'
export type AppointmentStatus = 'pending' | 'confirmed' | 'cancelled'

export interface Lead {
  id: number
  agency_id: string
  name: string | null
  phone: string | null
  email: string | null
  source_channel: string
  status: LeadStatus
  created_at: string
}

export interface Conversation {
  id: number
  lead_id: number
  current_state: ConversationState
  last_message_at: string
  messages: Message[]
}

export interface Message {
  id: number
  conversation_id: number
  direction: MessageDirection
  channel: string
  body: string
  created_at: string
}

export interface Appointment {
  id: number
  lead_id: number
  provider_event_id: string | null
  start_time: string | null
  end_time: string | null
  status: AppointmentStatus
}

export interface Summary {
  id: number
  lead_id: number
  summary_text: string
  summary_json: Record<string, unknown>
  created_at: string
}

// ---------------------------------------------------------------------------
// Fetchers (used with SWR)
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

async function apiPost<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST' })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export const getLeads = (agencyId: string) =>
  apiFetch<Lead[]>(`/leads?agency_id=${encodeURIComponent(agencyId)}`)

export const getLead = (leadId: number) =>
  apiFetch<Lead>(`/leads/${leadId}`)

export const getLeadConversations = (leadId: number) =>
  apiFetch<Conversation[]>(`/leads/${leadId}/conversations`)

export const getLeadAppointments = (leadId: number) =>
  apiFetch<Appointment[]>(`/leads/${leadId}/appointments`)

export const getLeadSummary = (leadId: number) =>
  apiFetch<Summary>(`/leads/${leadId}/summary`)

export const generateLeadSummary = (leadId: number) =>
  apiPost<Summary>(`/leads/${leadId}/summary`)

// ---------------------------------------------------------------------------
// SWR key factories
// ---------------------------------------------------------------------------

export const swrKeys = {
  leads: (agencyId: string) => `/leads?agency_id=${agencyId}`,
  lead: (leadId: number) => `/leads/${leadId}`,
  conversations: (leadId: number) => `/leads/${leadId}/conversations`,
  appointments: (leadId: number) => `/leads/${leadId}/appointments`,
  summary: (leadId: number) => `/leads/${leadId}/summary`,
}
