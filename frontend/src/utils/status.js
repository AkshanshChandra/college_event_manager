export const SUBMISSION_STATUS_META = {
  pending: { label: 'Pending', variant: 'neutral' },
  submitted: { label: 'Submitted', variant: 'success' },
  late: { label: 'Late', variant: 'danger' },
  closed: { label: 'Closed', variant: 'neutral' },
}

export const WINDOW_STATUS_META = {
  not_open: { label: 'Not Open Yet', variant: 'neutral' },
  open: { label: 'Open', variant: 'success' },
  closed: { label: 'Closed', variant: 'danger' },
}

export const ACCOUNT_STATUS_META = {
  not_created: { label: 'Not Created', variant: 'neutral' },
  pending_activation: { label: 'Pending Activation', variant: 'warning' },
  active: { label: 'Active', variant: 'success' },
  disabled: { label: 'Disabled', variant: 'danger' },
}

export const PUBLISH_STATUS_META = {
  draft: { label: 'Draft', variant: 'neutral' },
  published: { label: 'Published', variant: 'success' },
}

export const PAYMENT_STATUS_META = {
  pending: { label: 'No Proof Yet', variant: 'warning' },
  submitted: { label: 'Awaiting Verification', variant: 'accent' },
  paid: { label: 'Paid', variant: 'success' },
}

export function formatDateTime(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}
