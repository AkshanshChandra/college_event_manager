import { useEffect, useMemo, useState } from 'react'
import { Search, X } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Input } from '../../components/ui/Field'
import { Table, Td } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Dialog } from '../../components/ui/Dialog'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { ACCOUNT_STATUS_META, PAYMENT_STATUS_META } from '../../utils/status'

// The backend caps page_size at 200 — comfortably above this event's registration count.
const FETCH_ALL_PAGE_SIZE = 200

export function AdminMergeRegistrationsPage() {
  const { notify } = useToast()
  const [rows, setRows] = useState(null)
  const [search, setSearch] = useState('')
  const [primary, setPrimary] = useState(null)
  const [mergeTarget, setMergeTarget] = useState(null)
  const [merging, setMerging] = useState(false)

  const load = () => {
    setRows(null)
    adminApi.listRegistrations({ page: 1, page_size: FETCH_ALL_PAGE_SIZE }).then(({ data }) => setRows(data))
  }

  useEffect(load, [])

  const filtered = useMemo(() => {
    if (!rows) return []
    const list = primary ? rows.filter((r) => r.id !== primary.id) : rows
    if (!search.trim()) return list
    const q = search.trim().toLowerCase()
    return list.filter(
      (r) =>
        r.team_name.toLowerCase().includes(q) ||
        r.leader_name.toLowerCase().includes(q) ||
        r.leader_email.toLowerCase().includes(q) ||
        r.college.toLowerCase().includes(q)
    )
  }, [rows, primary, search])

  const handleMerge = async () => {
    if (!primary || !mergeTarget) return
    setMerging(true)
    try {
      const { data } = await adminApi.mergeRegistrations(primary.id, mergeTarget.id)
      notify(
        `Merged "${data.secondary_team_name}" into "${primary.team_name}" — ${data.members_moved} member(s) moved` +
          (data.submissions_discarded ? `, ${data.submissions_discarded} submission(s) discarded` : '') +
          (data.secondary_leader_disabled ? ', its leader login disabled.' : '.'),
        'success'
      )
      setMergeTarget(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not merge these registrations.'), 'error')
    } finally {
      setMerging(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Merge Registrations"
        description="Fold a duplicate registration into another — works at any stage, even before payment is verified, so merging never sends an activation email."
      />

      {primary && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-md border border-accent-100 bg-accent-100/40 px-4 py-3">
          <p className="text-sm text-ink-900">
            Keeping <span className="font-semibold">{primary.team_name}</span> ({primary.leader_email}) — pick a
            duplicate below to merge into it. You can merge more than one in a row.
          </p>
          <Button variant="secondary" size="sm" onClick={() => setPrimary(null)}>
            <X size={14} /> Change
          </Button>
        </div>
      )}

      <div className="relative mb-4 w-full max-w-xs">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
        <Input
          className="pl-9"
          placeholder="Search team, leader, email, college…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {rows === null ? (
        <PageLoader />
      ) : filtered.length === 0 ? (
        <EmptyState title="No registrations found" description="Try a different search." />
      ) : (
        <Table columns={['Team', 'Leader', 'Email', 'College', 'Domain', 'Size', 'Payment', 'Account', '']}>
          {filtered.map((r) => (
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
                <StatusBadge meta={PAYMENT_STATUS_META[r.payment_status]} />
              </Td>
              <Td>
                <StatusBadge meta={ACCOUNT_STATUS_META[r.account_status]} />
              </Td>
              <Td>
                {primary ? (
                  <Button variant="danger" size="sm" onClick={() => setMergeTarget(r)}>
                    Merge into {primary.team_name}
                  </Button>
                ) : (
                  <Button variant="secondary" size="sm" onClick={() => setPrimary(r)}>
                    Keep this one
                  </Button>
                )}
              </Td>
            </tr>
          ))}
        </Table>
      )}

      {mergeTarget && (
        <Dialog
          open
          onClose={() => setMergeTarget(null)}
          title="Merge registration"
          description={`Fold "${mergeTarget.team_name}" into "${primary.team_name}".`}
          footer={
            <>
              <Button variant="secondary" onClick={() => setMergeTarget(null)} disabled={merging}>
                Cancel
              </Button>
              <Button variant="danger" onClick={handleMerge} loading={merging}>
                Merge
              </Button>
            </>
          }
        >
          <div className="rounded-md border border-danger-100 bg-danger-100/40 p-3 text-sm text-ink-900">
            <p className="font-medium text-danger-600">This cannot be undone:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5">
              <li>
                {mergeTarget.leader_name} and {mergeTarget.team_name}'s members move onto {primary.team_name}.
              </li>
              <li>{mergeTarget.team_name}'s registration row is removed entirely.</li>
              <li>If it already has a Round 1 submission, that's discarded, not kept.</li>
              <li>If it already has an activated portal login, that login is disabled.</li>
              <li>
                {primary.team_name} keeps its own domain ({primary.domain_slug}) and payment status.
              </li>
            </ul>
          </div>
        </Dialog>
      )}
    </div>
  )
}
