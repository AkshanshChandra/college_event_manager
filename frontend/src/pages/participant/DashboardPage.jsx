import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { FileText, Lightbulb, UploadCloud, Clock, ArrowRight } from 'lucide-react'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, ErrorState } from '../../components/ui/States'
import { teamApi } from '../../services/team'
import { SUBMISSION_STATUS_META, formatDateTime } from '../../utils/status'

export function DashboardPage() {
  const { team } = useOutletContext()
  const [state, setState] = useState(null)
  const [hints, setHints] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    Promise.all([teamApi.getSubmissionState(), teamApi.getHints()])
      .then(([subRes, hintsRes]) => {
        setState(subRes.data)
        setHints(hintsRes.data)
      })
      .catch(() => setError(true))
  }, [])

  if (error) return <ErrorState description="Could not load your dashboard. Try refreshing." />
  if (!state) return <PageLoader />

  const latestHint = hints?.[hints.length - 1]
  const statusMeta = SUBMISSION_STATUS_META[state.participant_status]

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="text-2xl font-semibold text-ink-950">
        Welcome, {team ? team.name : 'Team'}
      </h1>
      <p className="mt-1 text-ink-500">Here's where things stand for Round 1.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryTile label="Domain" value={team?.domain?.name || '—'} />
        <SummaryTile label="Round" value="Round 1" />
        <SummaryTile label="Submission Status" value={<StatusBadge meta={statusMeta} />} />
        <SummaryTile label="Deadline" value={formatDateTime(state.submission_end)} icon={Clock} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card interactive>
          <CardHeader
            title="Problem Statement"
            action={<FileText size={18} className="text-ink-400" />}
          />
          <CardBody>
            <p className="text-sm text-ink-500">View the problem statement for your domain.</p>
            <Link to="/problem-statement">
              <Button variant="secondary" size="sm" className="mt-3">
                View Problem Statement <ArrowRight size={14} />
              </Button>
            </Link>
          </CardBody>
        </Card>

        <Card interactive>
          <CardHeader title="Latest Hint" action={<Lightbulb size={18} className="text-ink-400" />} />
          <CardBody>
            {latestHint ? (
              <>
                <p className="text-sm font-medium text-ink-900">
                  Week {latestHint.week_number}: {latestHint.title}
                </p>
                <p className="mt-1 line-clamp-2 text-sm text-ink-500">{latestHint.content}</p>
              </>
            ) : (
              <p className="text-sm text-ink-500">No hints published yet.</p>
            )}
            <Link to="/hints">
              <Button variant="secondary" size="sm" className="mt-3">
                View All Hints <ArrowRight size={14} />
              </Button>
            </Link>
          </CardBody>
        </Card>

        <Card interactive>
          <CardHeader title="Submission" action={<UploadCloud size={18} className="text-ink-400" />} />
          <CardBody>
            <p className="text-sm text-ink-500">
              {state.active_submission
                ? `Last submitted ${formatDateTime(state.active_submission.submitted_at)}.`
                : 'You have not submitted Round 1 yet.'}
            </p>
            <Link to="/submission">
              <Button variant="accent" size="sm" className="mt-3">
                {state.active_submission ? 'View / Update Submission' : 'Upload Submission'}{' '}
                <ArrowRight size={14} />
              </Button>
            </Link>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

function SummaryTile({ label, value, icon: Icon }) {
  return (
    <Card>
      <CardBody className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</p>
          <div className="mt-1 text-sm font-semibold text-ink-900">{value}</div>
        </div>
        {Icon && <Icon size={18} className="text-ink-300" />}
      </CardBody>
    </Card>
  )
}
