import { useEffect, useState } from 'react'
import { Search, Download, Image as ImageIcon } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Input, Select } from '../../components/ui/Field'
import { Table, Td } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { ACCOUNT_STATUS_META, PAYMENT_STATUS_META, formatDateTime } from '../../utils/status'

const PAGE_SIZE = 25

export function AdminRegistrationsPage() {
  const { notify } = useToast()
  const [rows, setRows] = useState(null)
  const [search, setSearch] = useState('')
  const [domain, setDomain] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [domains, setDomains] = useState([])
  const [page, setPage] = useState(1)
  const [updatingId, setUpdatingId] = useState(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
  }, [])

  const load = () => {
    setRows(null)
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (domain) params.domain = domain
    if (paymentMethod) params.payment_method = paymentMethod
    adminApi.listRegistrations(params).then(({ data }) => setRows(data))
  }

  useEffect(load, [search, domain, paymentMethod, page])

  const handleExportCsv = async () => {
    setExporting(true)
    try {
      const { data: blob } = await adminApi.exportRegistrationsCsv()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'adappt_registrations.csv'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      notify(getErrorMessage(err, 'Could not export registrations.'), 'error')
    } finally {
      setExporting(false)
    }
  }

  const setPaymentStatus = async (registration, next) => {
    setUpdatingId(registration.id)
    try {
      await adminApi.updatePaymentStatus(registration.id, next)
      notify(
        next === 'paid'
          ? "Marked as paid — credentials email sent to the team's leader."
          : 'Payment status updated.',
        'success'
      )
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not update payment status.'), 'error')
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Registrations"
        description="Teams registered through the portal's registration form."
        action={
          <Button variant="secondary" loading={exporting} onClick={handleExportCsv}>
            <Download size={16} /> Export CSV
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative w-full max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <Input
            className="pl-9"
            placeholder="Search team, leader, email…"
            value={search}
            onChange={(e) => {
              setPage(1)
              setSearch(e.target.value)
            }}
          />
        </div>
        <Select
          className="w-48"
          value={domain}
          onChange={(e) => {
            setPage(1)
            setDomain(e.target.value)
          }}
        >
          <option value="">All Domains</option>
          {domains.map((d) => (
            <option key={d.slug} value={d.slug}>
              {d.name}
            </option>
          ))}
        </Select>
        <Select
          className="w-44"
          value={paymentMethod}
          onChange={(e) => {
            setPage(1)
            setPaymentMethod(e.target.value)
          }}
        >
          <option value="">All Payment Methods</option>
          <option value="online">Online</option>
          <option value="cash">Cash</option>
        </Select>
      </div>

      {rows === null ? (
        <PageLoader />
      ) : rows.length === 0 ? (
        <EmptyState title="No registrations found" description="Try a different search or filter." />
      ) : (
        <Table columns={['Team', 'Leader', 'Email', 'College', 'Domain', 'Size', 'Payment', 'Registered', 'Account', '']}>
          {rows.map((r) => (
            <tr key={r.id}>
              <Td className="font-medium text-ink-900">{r.team_name}</Td>
              <Td>{r.leader_name}</Td>
              <Td>{r.leader_email}</Td>
              <Td>{r.college}</Td>
              <Td>
                <Badge variant="neutral">{r.domain_slug}</Badge>
              </Td>
              <Td>{r.team_size ?? '—'}</Td>
              <Td>
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    <StatusBadge meta={PAYMENT_STATUS_META[r.payment_status]} />
                    <Badge variant="neutral">{r.payment_method === 'cash' ? 'Cash' : 'Online'}</Badge>
                    {r.payment_amount_inr != null && (
                      <span className="text-xs text-ink-400">₹{r.payment_amount_inr}</span>
                    )}
                  </div>
                  {r.payment_screenshot_url && (
                    <a
                      href={r.payment_screenshot_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex w-fit items-center gap-1 text-xs font-medium text-accent-700 hover:underline"
                    >
                      <ImageIcon size={12} /> View Screenshot
                    </a>
                  )}
                </div>
              </Td>
              <Td>{formatDateTime(r.registered_at)}</Td>
              <Td>
                <StatusBadge meta={ACCOUNT_STATUS_META[r.account_status]} />
              </Td>
              <Td>
                <div className="flex gap-2">
                  {r.payment_status !== 'paid' && (
                    <Button
                      variant={r.payment_status === 'submitted' ? 'accent' : 'secondary'}
                      size="sm"
                      loading={updatingId === r.id}
                      onClick={() => setPaymentStatus(r, 'paid')}
                    >
                      Verify &amp; Send Credentials
                    </Button>
                  )}
                  {r.payment_status === 'paid' && (
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={updatingId === r.id}
                      onClick={() => setPaymentStatus(r, 'pending')}
                    >
                      Revert to Pending
                    </Button>
                  )}
                </div>
              </Td>
            </tr>
          ))}
        </Table>
      )}

      {rows && rows.length > 0 && (
        <div className="mt-4 flex items-center justify-between text-sm text-ink-500">
          <span>Page {page}</span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={rows.length < PAGE_SIZE}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
