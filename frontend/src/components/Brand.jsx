import { Link } from 'react-router-dom'

export function Brand({ to = '/', className = '' }) {
  return (
    <Link to={to} className={`inline-flex items-center gap-2 ${className}`}>
      <span className="flex h-7 w-7 items-center justify-center rounded-md bg-ink-900 text-xs font-bold text-white">
        A
      </span>
      <span className="text-base font-semibold tracking-tight text-ink-900">
        ADAPPT<span className="text-accent-600">.</span>
      </span>
    </Link>
  )
}
