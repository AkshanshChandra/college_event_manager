import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { Newspaper } from 'lucide-react'
import { Card, CardBody } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { PageLoader, EmptyState, ErrorState } from '../../components/ui/States'
import { teamApi } from '../../services/team'

export function BlogPage() {
  const { team } = useOutletContext()
  const [blog, setBlog] = useState(undefined) // undefined = loading, null = none published
  const [error, setError] = useState(false)

  useEffect(() => {
    teamApi
      .getBlog()
      .then(({ data }) => setBlog(data))
      .catch(() => setError(true))
  }, [])

  if (error) return <ErrorState description="Could not load the blog." />
  if (blog === undefined) return <PageLoader />

  return (
    <div className="mx-auto max-w-3xl">
      <Badge variant="accent">{team?.domain?.name}</Badge>
      <h1 className="mt-3 text-2xl font-semibold text-ink-950">Domain Blog</h1>

      {blog === null ? (
        <EmptyState
          icon={Newspaper}
          className="mt-6"
          title="No blog published yet"
          description="Your domain's background-reading article will appear here once organizers publish it."
        />
      ) : (
        <Card className="mt-6">
          <CardBody>
            <h2 className="text-lg font-semibold text-ink-950">{blog.title}</h2>
            <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-ink-700">{blog.content}</p>
          </CardBody>
        </Card>
      )}
    </div>
  )
}
