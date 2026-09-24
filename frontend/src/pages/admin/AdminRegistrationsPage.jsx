import { useEffect, useState } from 'react'
import { Search, Download } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Input, Select } from '../../components/ui/Field'
import { Table, Td } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { ACCOUNT_STATUS_META, formatDateTime } from '../../utils/status'

const PAGE_SIZE = 25

export function AdminRegistrationsPage() {
  const [rows, setRows] = useState(null)
  const [search, setSearch] = useState('')
  const [domain, setDomain] = useState('')
  const [domains, setDomains] = useState([])
  const [page, setPage] = useState(1)

  useEffect(() => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
  }, [])

  useEffect(() => {
    setRows(null)
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (domain) params.domain = domain
    adminApi.listRegistrations(params).then(({ data }) => setRows(data))
  }, [search, domain, page])

  return (
    <div>
      <PageHeader
        title="Registrations"
        description="Teams synced from the Google Form response sheet."
        action={
          <a href={adminApi.exportRegistrationsUrl()}>
            <Button variant="secondary">
              <Download size={16} /> Export CSV
            </Button>
          </a>
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
      </div>

      {rows === null ? (
        <PageLoader />
      ) : rows.length === 0 ? (
        <EmptyState title="No registrations found" description="Try a different search or filter." />
      ) : (
        <Table columns={['Team', 'Leader', 'Email', 'College', 'Domain', 'Registered', 'Account']}>
          {rows.map((r) => (
            <tr key={r.id}>
              <Td className="font-medium text-ink-900">{r.team_name}</Td>
              <Td>{r.leader_name}</Td>
              <Td>{r.leader_email}</Td>
              <Td>{r.college}</Td>
              <Td>
                <Badge variant="neutral">{r.domain_slug}</Badge>
              </Td>
              <Td>{formatDateTime(r.registered_at)}</Td>
              <Td>
                <StatusBadge meta={ACCOUNT_STATUS_META[r.account_status]} />
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
