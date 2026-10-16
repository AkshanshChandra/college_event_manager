import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Merge } from 'lucide-react'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Dialog } from '../../components/ui/Dialog'
import { Field, Select } from '../../components/ui/Field'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, ErrorState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { ACCOUNT_STATUS_META, SUBMISSION_STATUS_META, formatBytes, formatDateTime } from '../../utils/status'

export function AdminTeamDetailPage() {
  const { teamId } = useParams()
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(false)
  const [mergeOpen, setMergeOpen] = useState(false)

  const refetch = () => {
    setDetail(null)
    adminApi
      .getTeamDetail(teamId)
      .then(({ data }) => setDetail(data))
      .catch(() => setError(true))
  }

  useEffect(refetch, [teamId])

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
          <Button variant="secondary" size="sm" onClick={() => setMergeOpen(true)}>
            <Merge size={14} /> Merge another team in
          </Button>
        </div>
      </div>

      {mergeOpen && (
        <MergeTeamDialog
          primaryTeam={team}
          onClose={() => setMergeOpen(false)}
          onMerged={() => {
            setMergeOpen(false)
            refetch()
          }}
        />
      )}

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

function MergeTeamDialog({ primaryTeam, onClose, onMerged }) {
  const { notify } = useToast()
  const [otherTeams, setOtherTeams] = useState(null)
  const [secondaryTeamId, setSecondaryTeamId] = useState('')
  const [merging, setMerging] = useState(false)

  useEffect(() => {
    adminApi.listTeams().then(({ data }) => setOtherTeams(data.filter((t) => t.id !== primaryTeam.id)))
  }, [primaryTeam.id])

  const secondaryTeam = otherTeams?.find((t) => t.id === Number(secondaryTeamId))

  const handleMerge = async () => {
    if (!secondaryTeam) return
    setMerging(true)
    try {
      const { data } = await adminApi.mergeTeams(primaryTeam.id, secondaryTeam.id)
      notify(
        `Merged "${data.secondary_team_name}" into "${primaryTeam.name}" — ` +
          `${data.members_moved} member(s) moved, ${data.submissions_discarded} submission(s) discarded.`,
        'success'
      )
      onMerged()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not merge these teams.'), 'error')
    } finally {
      setMerging(false)
    }
  }

  return (
    <Dialog
      open
      onClose={onClose}
      title="Merge another team into this one"
      description={`Pick a duplicate team to fold into "${primaryTeam.name}".`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={merging}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleMerge} loading={merging} disabled={!secondaryTeam}>
            Merge
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Field label="Team to merge in" hint="Only teams with an activated portal account are listed.">
          <Select value={secondaryTeamId} onChange={(e) => setSecondaryTeamId(e.target.value)} disabled={!otherTeams}>
            <option value="">{otherTeams ? 'Select a team…' : 'Loading teams…'}</option>
            {otherTeams?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} — {t.domain.name} ({t.college})
              </option>
            ))}
          </Select>
        </Field>

        {secondaryTeam && (
          <div className="rounded-md border border-danger-200 bg-danger-50 p-3 text-sm text-danger-800">
            <p className="font-medium">This cannot be undone:</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5">
              <li>
                {secondaryTeam.name}'s members move onto {primaryTeam.name}.
              </li>
              <li>{secondaryTeam.name}'s submissions (if any) are discarded, not kept.</li>
              <li>{secondaryTeam.name}'s leader login is disabled.</li>
              <li>{primaryTeam.name} keeps its own domain ({primaryTeam.domain.name}).</li>
            </ul>
          </div>
        )}
      </div>
    </Dialog>
  )
}
