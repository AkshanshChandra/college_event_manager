export function PageHeader({ title, description, action }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-ink-950">{title}</h1>
        {description && <p className="mt-1 text-ink-500">{description}</p>}
      </div>
      {action}
    </div>
  )
}
