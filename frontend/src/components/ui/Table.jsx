export function Table({ columns, children }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-ink-200 bg-surface">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="border-b border-ink-100 bg-ink-50 text-xs font-medium uppercase tracking-wide text-ink-500">
          <tr>
            {columns.map((col) => (
              <th key={col} className="px-4 py-3">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink-100">{children}</tbody>
      </table>
    </div>
  )
}

export function Td({ children, className = '' }) {
  return <td className={`px-4 py-3 align-middle text-ink-800 ${className}`}>{children}</td>
}
