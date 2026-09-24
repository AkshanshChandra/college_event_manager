import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { FileDown } from 'lucide-react'
import { Card, CardBody } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { PageLoader, EmptyState, ErrorState } from '../../components/ui/States'
import { teamApi } from '../../services/team'

export function ProblemStatementPage() {
  const { team } = useOutletContext()
  const [ps, setPs] = useState(undefined)
  const [error, setError] = useState(false)

  useEffect(() => {
    teamApi
      .getProblemStatement()
      .then(({ data }) => setPs(data))
      .catch(() => setError(true))
  }, [])

  if (error) return <ErrorState description="Could not load the problem statement." />
  if (ps === undefined) return <PageLoader />

  if (ps === null) {
    return (
      <EmptyState
        title="Problem statement not published yet"
        description="Your domain's problem statement will appear here once organizers publish it."
      />
    )
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Badge variant="accent">{team?.domain?.name}</Badge>
      <h1 className="mt-3 text-2xl font-semibold text-ink-950">{ps.title}</h1>

      <Card className="mt-6">
        <CardBody className="flex flex-col gap-6">
          <Section title="Description" content={ps.description} />
          {ps.requirements && <Section title="Requirements" content={ps.requirements} />}
          {ps.constraints && <Section title="Constraints" content={ps.constraints} />}
          {ps.deliverables && <Section title="Deliverables" content={ps.deliverables} />}
          {ps.supporting_material_url && (
            <a
              href={ps.supporting_material_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-fit items-center gap-2 text-sm font-medium text-accent-700 hover:underline"
            >
              <FileDown size={16} /> Download supporting material
            </a>
          )}
        </CardBody>
      </Card>
    </div>
  )
}

function Section({ title, content }) {
  return (
    <div>
      <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-500">{title}</h2>
      <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-ink-800">{content}</p>
    </div>
  )
}
