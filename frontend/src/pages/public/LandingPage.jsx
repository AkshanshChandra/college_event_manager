import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, FileVideo, FileText, Lightbulb, ShieldCheck } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card, CardBody } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Skeleton } from '../../components/ui/States'
import { publicApi } from '../../services/team'
import { formatDateTime } from '../../utils/status'

const FAQS = [
  {
    q: 'Who can participate in ADAPPT?',
    a: 'ADAPPT is open to college teams. See the registration form for eligibility details specific to this edition.',
  },
  {
    q: 'How do I register?',
    a: 'Click "Register for ADAPPT" below to fill the official Google Form as a team. Your registered email becomes your portal login identifier.',
  },
  {
    q: 'Can I change my domain after registering?',
    a: 'No. Your domain is fixed at the time of registration and cannot be changed from the portal.',
  },
  {
    q: 'What do I submit for Round 1?',
    a: 'A PPT/PDF and a short demo video, uploaded through the participant portal before the deadline shown on your dashboard.',
  },
]

export function LandingPage() {
  const [domains, setDomains] = useState(null)
  const [timeline, setTimeline] = useState(null)

  useEffect(() => {
    publicApi
      .getDomains()
      .then(({ data }) => setDomains(data))
      .catch(() => setDomains([]))
    publicApi
      .getTimeline()
      .then(({ data }) => setTimeline(data))
      .catch(() => setTimeline(null))
  }, [])

  return (
    <div>
      {/* Hero */}
      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
        <div className="max-w-2xl">
          <Badge variant="accent">College Technology Competition</Badge>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink-950 sm:text-5xl">
            Build. Submit. Compete.
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-ink-600">
            ADAPPT is a team-based technology competition across three domains. Register your
            team, receive your problem statement, and submit your Round&nbsp;1 prototype directly
            through the participant portal.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href={timeline?.google_form_url || '#register'} target="_blank" rel="noreferrer">
              <Button variant="accent" size="lg">
                Register for ADAPPT <ArrowRight size={18} />
              </Button>
            </a>
            <Link to="/login">
              <Button variant="secondary" size="lg">
                Portal Login
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* About */}
      <section id="about" className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">About ADAPPT</h2>
          <p className="mt-3 max-w-3xl text-ink-600">
            ADAPPT challenges college teams to design and prototype real-world technology
            solutions within a fixed domain and timeline. Teams work through weekly hints, submit
            a working Round&nbsp;1 prototype, and are evaluated on both technical execution and
            problem understanding.
          </p>
        </div>
      </section>

      {/* Domains */}
      <section id="domains" className="py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Competition Domains</h2>
          <p className="mt-2 text-ink-600">Your domain is assigned based on your registration.</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {domains === null &&
              [0, 1, 2].map((i) => <Skeleton key={i} className="h-32 rounded-lg" />)}
            {domains?.length === 0 && (
              <p className="text-sm text-ink-500">Domains will be announced soon.</p>
            )}
            {domains?.map((d) => (
              <Card key={d.id}>
                <CardBody>
                  <h3 className="font-semibold text-ink-900">{d.name}</h3>
                  <p className="mt-1.5 text-sm text-ink-500">{d.description || 'Details coming soon.'}</p>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Structure / Round 1 */}
      <section className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Competition Structure</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <Card>
              <CardBody className="flex flex-col gap-2">
                <FileText size={20} className="text-accent-600" />
                <h3 className="font-medium text-ink-900">Round 1 · Prototype</h3>
                <p className="text-sm text-ink-500">
                  Submit a PPT/PDF outlining your solution to your domain's problem statement.
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody className="flex flex-col gap-2">
                <FileVideo size={20} className="text-accent-600" />
                <h3 className="font-medium text-ink-900">Demo Video</h3>
                <p className="text-sm text-ink-500">
                  A short recorded walkthrough of your working prototype.
                </p>
              </CardBody>
            </Card>
            <Card>
              <CardBody className="flex flex-col gap-2">
                <Lightbulb size={20} className="text-accent-600" />
                <h3 className="font-medium text-ink-900">Weekly Hints</h3>
                <p className="text-sm text-ink-500">
                  Organizers publish guidance each week to help teams stay on track.
                </p>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>

      {/* Timeline / Submission info */}
      <section id="timeline" className="py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Timeline &amp; Submission</h2>
          <Card className="mt-6">
            <CardBody className="grid gap-6 sm:grid-cols-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-ink-500">Round 1 Opens</p>
                <p className="mt-1 font-medium text-ink-900">
                  {timeline ? formatDateTime(timeline.submission_start) : '[SUBMISSION START]'}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-ink-500">Round 1 Deadline</p>
                <p className="mt-1 font-medium text-ink-900">
                  {timeline ? formatDateTime(timeline.submission_end) : '[SUBMISSION DEADLINE]'}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-ink-500">Status</p>
                <p className="mt-1">
                  <Badge variant={timeline?.submission_window_status === 'open' ? 'success' : 'neutral'}>
                    {timeline?.submission_window_status === 'open' ? 'Submissions Open' : 'Not Open'}
                  </Badge>
                </p>
              </div>
            </CardBody>
          </Card>
        </div>
      </section>

      {/* Security note / trust */}
      <section className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto flex max-w-6xl items-start gap-4 px-4 sm:px-6">
          <ShieldCheck size={24} className="mt-1 shrink-0 text-accent-600" />
          <p className="text-sm text-ink-600">
            Portal access is only granted to the email address used at registration. If you
            haven't set up your portal account yet, use the <Link to="/login" className="font-medium text-accent-700 underline">Portal Login</Link> page
            to request an activation link.
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Frequently Asked Questions</h2>
          <div className="mt-6 divide-y divide-ink-100 rounded-lg border border-ink-200 bg-surface">
            {FAQS.map((item) => (
              <details key={item.q} className="group px-5 py-4">
                <summary className="cursor-pointer list-none text-sm font-medium text-ink-900">
                  {item.q}
                </summary>
                <p className="mt-2 text-sm text-ink-500">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Register CTA */}
      <section id="register" className="border-t border-ink-100 bg-ink-950 py-16">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-4 sm:flex-row sm:items-center sm:px-6">
          <div>
            <h2 className="text-2xl font-semibold text-white">Ready to compete?</h2>
            <p className="mt-2 text-ink-300">Register your team through the official form.</p>
          </div>
          <a href={timeline?.google_form_url || '#'} target="_blank" rel="noreferrer">
            <Button variant="accent" size="lg">
              Register for ADAPPT <ArrowRight size={18} />
            </Button>
          </a>
        </div>
      </section>
    </div>
  )
}
