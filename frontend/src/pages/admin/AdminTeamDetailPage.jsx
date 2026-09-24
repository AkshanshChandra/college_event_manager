import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, ErrorState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { ACCOUNT_STATUS_META, SUBMISSION_STATUS_META, formatBytes, formatDateTime } from '../../utils/status'

export function AdminTeamDetailPage() {
  const { teamId } = useParams()
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    adminApi
      .getTeamDetail(teamId)
      .then(({ data }) => setDetail(data))
      .catch(() => setError(true))
  }, [teamId])

  if (error) return <ErrorState description="Could not load this team." />
  if (!detail) return <PageLoader />

  const { team, account_status, submissions } = detail
  const activeSubmission = submissions.find((s) => s.is_active_version)

  return (
    <div>
      <Link to="/admin/teams" className="mb-4 inline-flex items-center gap-1 text-sm text-ink-500 hover:text-ink-900">
        <ArrowLeft size={14} /> Back to Teams
      </Link>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-ink-950">{team.name}</h1>
          <p className="mt-1 text-ink-500">{team.college}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="accent">{team.domain.name}</Badge>
          <StatusBadge meta={ACCOUNT_STATUS_META[account_status]} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Team Leader" />
          <CardBody className="flex flex-col gap-2 text-sm">
            <Row label="Name" value={team.leader_name} />
            <Row label="Email" value={team.leader_email} />
            <Row label="Phone" value={team.leader_phone} />
            <Row label="Registered" value={formatDateTime(team.registered_at)} />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Team Members" />
          <CardBody>
            <ul className="divide-y divide-ink-100 text-sm">
              {team.members.map((m) => (
                <li key={m.id} className="py-1.5 text-ink-800">
                  {m.name}
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader
          title="Submission"
          description={activeSubmission ? `Active version ${activeSubmission.version}` : 'No submission yet'}
          action={activeSubmission && <StatusBadge meta={SUBMISSION_STATUS_META[activeSubmission.status]} />}
        />
        <CardBody className="flex flex-col divide-y divide-ink-100">
          {submissions.length === 0 && <p className="text-sm text-ink-500">This team has not submitted yet.</p>}
          {[...submissions].reverse().map((s) => (
            <div key={s.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
              <div>
                <span className="font-medium text-ink-900">Version {s.version}</span>
                {s.is_active_version && (
                  <Badge variant="accent" className="ml-2">
                    Active
                  </Badge>
                )}
                <p className="text-xs text-ink-500">{formatDateTime(s.submitted_at)}</p>
              </div>
              <div className="flex flex-col items-end gap-0.5 text-xs text-ink-500">
                {s.files.map((f) => (
                  <span key={f.id}>
                    {f.file_type}: {f.original_filename} ({formatBytes(f.file_size_bytes)})
                  </span>
                ))}
              </div>
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-500">{label}</span>
      <span className="font-medium text-ink-900">{value}</span>
    </div>
  )
}
