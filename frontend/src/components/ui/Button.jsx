import { Loader2 } from 'lucide-react'

const VARIANTS = {
  primary: 'bg-ink-900 text-white hover:bg-ink-800 disabled:bg-ink-300',
  accent: 'bg-accent-600 text-white hover:bg-accent-700 disabled:bg-accent-400/60',
  secondary: 'bg-white text-ink-900 border border-ink-200 hover:bg-ink-50 disabled:text-ink-300',
  ghost: 'text-ink-700 hover:bg-ink-100 disabled:text-ink-300',
  danger: 'bg-danger-600 text-white hover:brightness-95 disabled:bg-danger-600/50',
}

const SIZES = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-11 px-5 text-base gap-2',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  children,
  ...props
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center rounded-md font-medium transition-colors
        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500
        disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {loading && <Loader2 size={16} className="animate-spin" />}
      {children}
    </button>
  )
}
