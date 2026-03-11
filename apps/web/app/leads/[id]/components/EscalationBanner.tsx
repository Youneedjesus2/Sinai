import { AlertTriangle } from 'lucide-react'

interface Props {
  reasons: string[]
}

export function EscalationBanner({ reasons }: Props) {
  return (
    <div className="flex gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
      <div>
        <p className="font-semibold text-red-800">Escalation Required</p>
        {reasons.length > 0 && (
          <ul className="mt-1 list-inside list-disc text-sm text-red-700">
            {reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
