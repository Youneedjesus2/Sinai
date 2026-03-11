import { NextRequest, NextResponse } from 'next/server'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function POST(request: NextRequest) {
  let leadId: number
  try {
    const body = (await request.json()) as { leadId?: unknown }
    if (typeof body.leadId !== 'number' || !Number.isInteger(body.leadId) || body.leadId <= 0) {
      return NextResponse.json({ error: 'leadId must be a positive integer' }, { status: 400 })
    }
    leadId = body.leadId
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const upstream = await fetch(`${API_BASE}/leads/${leadId}/summary`, {
    method: 'POST',
  })

  const data: unknown = await upstream.json()

  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status })
  }

  return NextResponse.json(data, { status: 200 })
}
