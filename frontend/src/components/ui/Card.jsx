export function Card({ interactive = false, className = '', children, ...props }) {
  return (
    <div
      className={`rounded-lg border border-ink-200 bg-surface shadow-[0_1px_3px_rgba(0,0,0,0.3)] transition-all duration-200 ${
        interactive
          ? 'hover:-translate-y-0.5 hover:border-accent-500/40 hover:shadow-[0_10px_28px_-6px_rgba(201,44,55,0.18)]'
          : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ title, description, action, className = '' }) {
  return (
    <div className={`flex items-start justify-between gap-4 border-b border-ink-100 px-5 py-4 ${className}`}>
      <div>
        <h3 className="text-sm font-semibold text-ink-900">{title}</h3>
        {description && <p className="mt-0.5 text-sm text-ink-500">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export function CardBody({ className = '', children }) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>
}
