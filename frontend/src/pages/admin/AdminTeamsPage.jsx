import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Input } from '../../components/ui/Field'
import { Table, Td } from '../../components/ui/Table'
import { Badge } from '../../components/ui/Badge'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { formatDateTime } from '../../utils/status'

export function AdminTeamsPage() {
  const [teams, setTeams] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    setTeams(null)
    const params = search ? { search } : {}
    adminApi.listTeams(params).then(({ data }) => setTeams(data))
  }, [search])

  return (
    <div>
      <PageHeader title="Teams" description="Teams that have activated a portal account." />

      <div className="relative mb-4 w-full max-w-xs">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
        <Input className="pl-9" placeholder="Search team name…" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {teams === null ? (
        <PageLoader />
      ) : teams.length === 0 ? (
        <EmptyState title="No teams yet" description="Teams appear here once a leader activates portal access." />
      ) : (
        <Table columns={['Team', 'Domain', 'College', 'Leader', 'Registered', '']}>
          {teams.map((t) => (
            <tr key={t.id}>
              <Td className="font-medium text-ink-900">{t.name}</Td>
              <Td>
                <Badge variant="accent">{t.domain.name}</Badge>
              </Td>
              <Td>{t.college}</Td>
              <Td>{t.leader_name}</Td>
              <Td>{formatDateTime(t.registered_at)}</Td>
              <Td>
                <Link to={`/admin/teams/${t.id}`} className="font-medium text-accent-700 hover:underline">
                  View
                </Link>
              </Td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  )
}
