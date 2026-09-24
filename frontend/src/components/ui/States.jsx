import { Loader2, Inbox, AlertTriangle } from 'lucide-react'

export function Spinner({ size = 20, className = '' }) {
  return <Loader2 size={size} className={`animate-spin text-ink-400 ${className}`} />
}

export function PageLoader({ label = 'Loading…' }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 py-24 text-ink-500">
      <Spinner size={24} />
      <p className="text-sm">{label}</p>
    </div>
  )
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, className = '' }) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink-200 px-6 py-14 text-center ${className}`}
    >
      <Icon size={28} className="text-ink-300" />
      <p className="text-sm font-medium text-ink-800">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-500">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

export function ErrorState({ title = 'Something went wrong', description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-danger-100 bg-danger-100/40 px-6 py-14 text-center">
      <AlertTriangle size={28} className="text-danger-600" />
      <p className="text-sm font-medium text-ink-800">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-500">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-md bg-ink-100 ${className}`} />
}
