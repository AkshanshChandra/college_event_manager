import { useOutletContext } from 'react-router-dom'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { PageLoader } from '../../components/ui/States'
import { formatDateTime } from '../../utils/status'

export function TeamPage() {
  const { team } = useOutletContext()

  if (!team) return <PageLoader />

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold text-ink-950">{team.name}</h1>
      <p className="mt-1 text-ink-500">{team.college}</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader title="Team Details" />
          <CardBody className="flex flex-col gap-3 text-sm">
            <Row label="Domain"><Badge variant="accent">{team.domain.name}</Badge></Row>
            <Row label="College" value={team.college} />
            <Row label="Registered On" value={formatDateTime(team.registered_at)} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Team Leader" />
          <CardBody className="flex flex-col gap-3 text-sm">
            <Row label="Name" value={team.leader_name} />
            <Row label="Email" value={team.leader_email} />
            <Row label="Phone" value={team.leader_phone} />
          </CardBody>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader title="Team Members" description={`${team.members.length} member(s)`} />
        <CardBody>
          <ul className="divide-y divide-ink-100">
            {team.members.map((m) => (
              <li key={m.id} className="flex items-center justify-between py-2 text-sm">
                <span className="text-ink-900">{m.name}</span>
                {m.email && <span className="text-ink-500">{m.email}</span>}
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>
    </div>
  )
}

function Row({ label, value, children }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-500">{label}</span>
      {children || <span className="font-medium text-ink-900">{value}</span>}
    </div>
  )
}
