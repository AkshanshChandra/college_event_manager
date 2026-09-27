import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { FileDown } from 'lucide-react'
import { Card, CardBody } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { PageLoader, EmptyState, ErrorState } from '../../components/ui/States'
import { teamApi } from '../../services/team'

export function ProblemStatementPage() {
  const { team } = useOutletContext()
  const [statements, setStatements] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    teamApi
      .getProblemStatements()
      .then(({ data }) => setStatements(data))
      .catch(() => setError(true))
  }, [])

  if (error) return <ErrorState description="Could not load your problem statements." />
  if (statements === null) return <PageLoader />

  return (
    <div className="mx-auto max-w-3xl">
      <Badge variant="accent">{team?.domain?.name}</Badge>
      <h1 className="mt-3 text-2xl font-semibold text-ink-950">{team?.domain?.name}</h1>
      {team?.domain?.description && (
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-500">{team.domain.description}</p>
      )}

      {statements.length === 0 ? (
        <EmptyState
          className="mt-6"
          title="Problem statements not published yet"
          description="Your domain's problem statements will appear here once organizers publish them."
        />
      ) : (
        <div className="mt-6 flex flex-col gap-4">
          {statements.map((ps, i) => (
            <Card key={ps.id} interactive>
              <CardBody className="flex flex-col gap-4">
                <div className="flex items-start gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-accent-600/40 bg-accent-600/10 text-sm font-semibold text-accent-500">
                    {i + 1}
                  </span>
                  <h2 className="mt-1 text-lg font-semibold text-ink-950">{ps.title}</h2>
                </div>

                <Section title="Description" content={ps.description} />
                {ps.requirements && <Section title="Requirements" content={ps.requirements} />}
                {ps.constraints && <Section title="Constraints" content={ps.constraints} />}
                {ps.deliverables && <Section title="Deliverables" content={ps.deliverables} />}
                {ps.supporting_material_url && (
                  <a
                    href={ps.supporting_material_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex w-fit items-center gap-2 text-sm font-medium text-accent-500 hover:underline"
                  >
                    <FileDown size={16} /> Download supporting material
                  </a>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function Section({ title, content }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-500">{title}</h3>
      <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-ink-700">{content}</p>
    </div>
  )
}
