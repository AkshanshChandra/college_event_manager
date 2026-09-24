export function Card({ className = '', children, ...props }) {
  return (
    <div
      className={`rounded-lg border border-ink-200 bg-surface shadow-[0_1px_2px_rgba(15,23,32,0.04)] ${className}`}
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
