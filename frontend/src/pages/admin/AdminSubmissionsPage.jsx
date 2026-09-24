import { useEffect, useState } from 'react'
import { Search, Download, Eye } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Input, Select } from '../../components/ui/Field'
import { Table, Td } from '../../components/ui/Table'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Dialog } from '../../components/ui/Dialog'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { SUBMISSION_STATUS_META, formatBytes, formatDateTime } from '../../utils/status'

export function AdminSubmissionsPage() {
  const [rows, setRows] = useState(null)
  const [domains, setDomains] = useState([])
  const [search, setSearch] = useState('')
  const [domain, setDomain] = useState('')
  const [detailId, setDetailId] = useState(null)
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
  }, [])

  useEffect(() => {
    setRows(null)
    const params = {}
    if (search) params.search = search
    if (domain) params.domain_slug = domain
    adminApi.listSubmissions(params).then(({ data }) => setRows(data))
  }, [search, domain])

  useEffect(() => {
    if (detailId) adminApi.getSubmissionDetail(detailId).then(({ data }) => setDetail(data))
    else setDetail(null)
  }, [detailId])

  return (
    <div>
      <PageHeader title="Submissions" description="Active Round 1 submissions from every team." />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative w-full max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <Input className="pl-9" placeholder="Search team…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Select className="w-48" value={domain} onChange={(e) => setDomain(e.target.value)}>
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
        <EmptyState title="No submissions yet" description="Submissions will appear here as teams submit." />
      ) : (
        <Table columns={['Team', 'Domain', 'Status', 'Submitted At', 'Version', '']}>
          {rows.map((r) => (
            <tr key={r.submission_id}>
              <Td className="font-medium text-ink-900">{r.team_name}</Td>
              <Td>
                <Badge variant="accent">{r.domain}</Badge>
              </Td>
              <Td>
                <StatusBadge meta={SUBMISSION_STATUS_META[r.status]} />
              </Td>
              <Td>{formatDateTime(r.submitted_at)}</Td>
              <Td>v{r.version}</Td>
              <Td>
                <button
                  onClick={() => setDetailId(r.submission_id)}
                  className="flex items-center gap-1 font-medium text-accent-700 hover:underline"
                >
                  <Eye size={14} /> View
                </button>
              </Td>
            </tr>
          ))}
        </Table>
      )}

      <Dialog open={Boolean(detailId)} onClose={() => setDetailId(null)} title={detail ? `${detail.team_name} — Version ${detail.version}` : 'Loading…'}>
        {!detail ? (
          <PageLoader />
        ) : (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-ink-500">Submitted {formatDateTime(detail.submitted_at)}</p>
            {detail.files.map((f) => (
              <div key={f.id} className="flex items-center justify-between rounded-md border border-ink-100 px-3 py-2">
                <div>
                  <p className="text-sm font-medium capitalize text-ink-900">{f.file_type}</p>
                  <p className="text-xs text-ink-500">
                    {f.original_filename} · {formatBytes(f.file_size_bytes)}
                  </p>
                </div>
                <a
                  href={f.download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-sm font-medium text-accent-700 hover:underline"
                >
                  <Download size={14} /> Download
                </a>
              </div>
            ))}
          </div>
        )}
      </Dialog>
    </div>
  )
}
