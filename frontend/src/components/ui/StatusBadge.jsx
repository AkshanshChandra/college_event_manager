import { Badge } from './Badge'

export function StatusBadge({ meta }) {
  if (!meta) return null
  return <Badge variant={meta.variant}>{meta.label}</Badge>
}
