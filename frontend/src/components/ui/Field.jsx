export function Field({ label, htmlFor, error, hint, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={htmlFor} className="text-sm font-medium text-ink-800">
          {label}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-ink-500">{hint}</p>}
      {error && <p className="text-xs text-danger-600">{error}</p>}
    </div>
  )
}

const baseInputClasses =
  'h-10 w-full rounded-md border border-ink-200 bg-white px-3 text-sm text-ink-900 placeholder:text-ink-400 ' +
  'focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-100 disabled:bg-ink-50 disabled:text-ink-400'

export function Input({ className = '', ...props }) {
  return <input className={`${baseInputClasses} ${className}`} {...props} />
}

export function Textarea({ className = '', rows = 4, ...props }) {
  return <textarea rows={rows} className={`${baseInputClasses} h-auto py-2 ${className}`} {...props} />
}

export function Select({ className = '', children, ...props }) {
  return (
    <select className={`${baseInputClasses} ${className}`} {...props}>
      {children}
    </select>
  )
}
