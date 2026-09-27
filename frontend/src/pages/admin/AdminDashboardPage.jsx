import { useCallback, useEffect, useState } from 'react'
import { RefreshCw, Users, FileCheck, Clock, Layers } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, ErrorState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { WINDOW_STATUS_META, formatDateTime } from '../../utils/status'

export function AdminDashboardPage() {
  const { notify } = useToast()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const load = useCallback(() => {
    adminApi
      .getDashboard()
      .then(({ data }) => setStats(data))
      .catch(() => setError(true))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleSync = async () => {
    setSyncing(true)
    try {
      const { data } = await adminApi.pushRegistrationsToSheet()
      notify(`Pushed ${data.rows_synced} registration(s) to the Google Sheet.`, 'success')
    } catch (err) {
      notify(getErrorMessage(err, 'Could not push to Google Sheet.'), 'error')
    } finally {
      setSyncing(false)
    }
  }

  if (error) return <ErrorState description="Could not load dashboard stats." />
  if (!stats) return <PageLoader />

  const maxDomainCount = Math.max(1, ...Object.values(stats.registrations_by_domain))

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Live registration and submission statistics."
        action={
          <Button variant="secondary" onClick={handleSync} loading={syncing}>
            <RefreshCw size={16} /> Push to Google Sheet
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile icon={Users} label="Total Registrations" value={stats.total_registrations} />
        <StatTile icon={FileCheck} label="Submitted Teams" value={stats.submitted_teams} />
        <StatTile icon={Clock} label="Pending Teams" value={stats.pending_teams} />
        <StatTile icon={Layers} label="Late Teams" value={stats.late_teams} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Registrations by Domain" />
          <CardBody className="flex flex-col gap-3">
            {Object.entries(stats.registrations_by_domain).length === 0 && (
              <p className="text-sm text-ink-500">No registrations yet.</p>
            )}
            {Object.entries(stats.registrations_by_domain).map(([domain, count]) => (
              <div key={domain}>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-ink-800">{domain}</span>
                  <span className="text-ink-500">{count}</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-ink-100">
                  <div
                    className="h-full rounded-full bg-accent-600"
                    style={{ width: `${(count / maxDomainCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Round 1 Status" />
          <CardBody className="flex flex-col gap-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-ink-500">Submission Window</span>
              <StatusBadge meta={WINDOW_STATUS_META[stats.submission_window_status]} />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-ink-500">Deadline</span>
              <span className="font-medium text-ink-900">{formatDateTime(stats.submission_end)}</span>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

function StatTile({ icon: Icon, label, value }) {
  return (
    <Card>
      <CardBody className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</p>
          <p className="mt-1 text-2xl font-semibold text-ink-950">{value}</p>
        </div>
        <Icon size={20} className="text-ink-300" />
      </CardBody>
    </Card>
  )
}
