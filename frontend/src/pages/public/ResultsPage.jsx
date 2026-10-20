import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Trophy, Sparkles, Clock, ArrowRight, Lock, UtensilsCrossed, Bot, Lightbulb, GraduationCap } from 'lucide-react'
import { Card, CardBody } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Skeleton } from '../../components/ui/States'
import { publicApi } from '../../services/team'

const DOMAIN_ICONS = {
  'cybersecurity-smart-homes': Lock,
  'ai-foodtech': UtensilsCrossed,
  'robotics-disaster-management': Bot,
}

function useInView(threshold = 0.15) {
  const ref = useRef(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          observer.disconnect()
        }
      },
      { threshold }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold])

  return [ref, inView]
}

function Reveal({ as: As = 'div', delay = 0, className = '', children }) {
  const [ref, inView] = useInView()
  return (
    <As
      ref={ref}
      className={`${inView ? 'animate-fade-in-up' : 'opacity-0'} ${className}`}
      style={inView ? { animationDelay: `${delay}ms` } : undefined}
    >
      {children}
    </As>
  )
}

export function ResultsPage() {
  const [results, setResults] = useState(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    publicApi
      .getResults()
      .then(({ data }) => setResults(data))
      .catch(() => setError(true))
  }, [])

  const groups = {}
  if (results?.teams) {
    for (const t of results.teams) {
      const key = t.domain.slug
      if (!groups[key]) groups[key] = { domain: t.domain, teams: [] }
      groups[key].teams.push(t)
    }
  }
  const groupList = Object.values(groups)

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 grid-overlay" />
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[560px] w-[560px] -translate-x-1/2 glow-accent" />
        <div className="pointer-events-none absolute inset-0 confetti-dots" />

        <div className="relative mx-auto max-w-5xl px-4 py-20 text-center sm:px-6 sm:py-28">
          <div className="animate-fade-in-up">
            <span className="trophy-pulse mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-accent-600/30 bg-accent-600/10 text-accent-500">
              <Trophy size={30} />
            </span>
            <Badge variant="accent" className="mt-5">
              ADAPPT 5.0 · Round 1
            </Badge>
            <h1 className="mx-auto mt-5 max-w-3xl text-5xl font-extrabold leading-[1.05] tracking-tight text-ink-950 sm:text-6xl">
              THE RESULTS
              <br />
              ARE <span className="text-gradient-accent">IN.</span>
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-ink-600">
              {results?.announcement ||
                'Congratulations to every team that pitched an idea. Here are the teams moving forward to Round 2 — Tech Twists.'}
            </p>
          </div>
        </div>
      </section>

      {/* Body */}
      <section className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          {results === null && !error && (
            <div className="flex flex-col gap-6">
              {[0, 1].map((i) => (
                <div key={i} className="flex flex-col gap-3">
                  <Skeleton className="h-6 w-48" />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Skeleton className="h-20 rounded-lg" />
                    <Skeleton className="h-20 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && (
            <EmptyNotice
              icon={Clock}
              title="Couldn't load results right now"
              description="Please refresh the page in a moment."
            />
          )}

          {results && !error && !results.is_published && (
            <EmptyNotice
              icon={Clock}
              title="Results haven't been announced yet"
              description="Round 1 is still being evaluated. Check back here once judging wraps up — qualified teams will also be notified by email."
            />
          )}

          {results && results.is_published && groupList.length === 0 && (
            <EmptyNotice
              icon={Sparkles}
              title="Results are being finalized"
              description="The qualified-teams list will appear here shortly."
            />
          )}

          {results &&
            results.is_published &&
            groupList.length > 0 &&
            groupList.map((group, gi) => {
              const Icon = DOMAIN_ICONS[group.domain.slug] || Lightbulb
              return (
                <Reveal key={group.domain.id} delay={gi * 80} className="mb-12 last:mb-0">
                  <div className="mb-5 flex items-center gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-accent-600/30 bg-accent-600/10 text-accent-500">
                      <Icon size={19} />
                    </span>
                    <div>
                      <h2 className="text-xl font-semibold text-ink-950">{group.domain.name}</h2>
                      <p className="text-sm text-ink-500">
                        {group.teams.length} team{group.teams.length === 1 ? '' : 's'} qualified for Round 2
                      </p>
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    {group.teams.map((t, ti) => (
                      <Reveal key={t.id} delay={gi * 80 + ti * 50 + 100}>
                        <Card interactive className="h-full">
                          <CardBody className="flex items-start gap-3">
                            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-600/10 text-xs font-bold text-accent-500">
                              {String(ti + 1).padStart(2, '0')}
                            </span>
                            <div className="min-w-0">
                              <p className="truncate font-semibold text-ink-900">{t.team_name}</p>
                              {t.college && (
                                <p className="mt-0.5 flex items-center gap-1 text-xs text-ink-500">
                                  <GraduationCap size={12} className="shrink-0" />
                                  <span className="truncate">{t.college}</span>
                                </p>
                              )}
                            </div>
                          </CardBody>
                        </Card>
                      </Reveal>
                    ))}
                  </div>
                </Reveal>
              )
            })}
        </div>
      </section>

      {/* CTA */}
      {results?.is_published && groupList.length > 0 && (
        <section className="py-16">
          <div className="mx-auto max-w-5xl px-4 sm:px-6">
            <div className="relative overflow-hidden rounded-2xl border border-accent-600/25 bg-gradient-to-br from-accent-600/15 via-transparent to-transparent px-6 py-10 sm:px-10">
              <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full glow-accent" />
              <div className="relative flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
                <div>
                  <h2 className="text-2xl font-semibold text-ink-950">Qualified for Round 2?</h2>
                  <p className="mt-2 text-ink-500">
                    Log in to the participant portal for your Round 2 briefing and next steps.
                  </p>
                </div>
                <Link to="/login">
                  <Button variant="accent" size="lg">
                    Portal Login <ArrowRight size={18} />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

function EmptyNotice({ icon: Icon, title, description }) {
  return (
    <Reveal>
      <div className="mx-auto flex max-w-md flex-col items-center gap-3 rounded-2xl border border-dashed border-ink-200 bg-paper px-6 py-16 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full border border-accent-600/30 bg-accent-600/10 text-accent-500">
          <Icon size={22} />
        </span>
        <p className="text-base font-semibold text-ink-900">{title}</p>
        <p className="text-sm text-ink-500">{description}</p>
        <Link to="/" className="mt-2 text-sm font-medium text-accent-500 hover:underline">
          Back to home
        </Link>
      </div>
    </Reveal>
  )
}
