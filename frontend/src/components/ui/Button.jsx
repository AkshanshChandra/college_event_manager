import { Loader2 } from 'lucide-react'

const VARIANTS = {
  primary: 'bg-white text-black hover:bg-ink-800 disabled:bg-ink-300 disabled:text-ink-500',
  accent:
    'bg-accent-600 text-white shadow-[0_0_0_0_rgba(201,44,55,0)] hover:bg-accent-700 hover:shadow-[0_4px_20px_-2px_rgba(201,44,55,0.45)] disabled:bg-accent-400/60 disabled:shadow-none',
  secondary: 'bg-transparent text-ink-900 border border-ink-300 hover:bg-ink-100 disabled:text-ink-500 disabled:border-ink-200',
  ghost: 'text-ink-400 hover:bg-ink-100 hover:text-ink-950 disabled:text-ink-600',
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
      className={`inline-flex items-center justify-center rounded-md font-medium transition-all duration-150 active:scale-[0.97]
        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500
        disabled:cursor-not-allowed disabled:active:scale-100 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {loading && <Loader2 size={16} className="animate-spin" />}
      {children}
    </button>
  )
}
