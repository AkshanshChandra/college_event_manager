import { Link } from 'react-router-dom'
import adapptLogo from '../assets/brand/adappt-logo.png'

export function Brand({ to = '/', className = '' }) {
  return (
    <Link to={to} className={`inline-flex items-center gap-2 ${className}`}>
      <img src={adapptLogo} alt="ADAPPT" className="h-7 w-auto" />
      <span className="text-base font-semibold tracking-tight text-ink-950">
        ADAPPT<span className="text-accent-600">.</span>
      </span>
    </Link>
  )
}
