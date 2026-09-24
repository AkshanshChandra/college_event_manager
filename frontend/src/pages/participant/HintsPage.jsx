import { useEffect, useState } from 'react'
import { Lightbulb } from 'lucide-react'
import { Card, CardBody } from '../../components/ui/Card'
import { PageLoader, EmptyState, ErrorState } from '../../components/ui/States'
import { teamApi } from '../../services/team'
import { formatDateTime } from '../../utils/status'

export function HintsPage() {
  const [hints, setHints] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    teamApi
      .getHints()
      .then(({ data }) => setHints(data))
      .catch(() => setError(true))
  }, [])

  if (error) return <ErrorState description="Could not load hints." />
  if (!hints) return <PageLoader />

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold text-ink-950">Weekly Hints</h1>
      <p className="mt-1 text-ink-500">Guidance published by the organizing committee.</p>

      {hints.length === 0 ? (
        <EmptyState
          icon={Lightbulb}
          className="mt-6"
          title="No hints published yet"
          description="Check back later — organizers publish hints on a weekly cadence."
        />
      ) : (
        <div className="mt-6 flex flex-col gap-4">
          {hints.map((hint) => (
            <Card key={hint.id}>
              <CardBody>
                <div className="flex items-baseline justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-accent-600">
                    Week {hint.week_number}
                  </p>
                  <p className="text-xs text-ink-400">{formatDateTime(hint.publish_at)}</p>
                </div>
                <h2 className="mt-1 text-base font-semibold text-ink-900">{hint.title}</h2>
                <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-ink-600">
                  {hint.content}
                </p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
