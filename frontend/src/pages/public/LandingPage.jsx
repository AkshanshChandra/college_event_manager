import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Lightbulb,
  ShieldCheck,
  Lock,
  UtensilsCrossed,
  Bot,
  MapPin,
  CalendarDays,
  Users,
  Trophy,
  Video,
  Wrench,
} from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card, CardBody } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Skeleton } from '../../components/ui/States'
import { publicApi } from '../../services/team'
import { formatDateTime } from '../../utils/status'

const FAQS = [
  {
    q: 'Who can participate in ADAPPT?',
    a: 'ADAPPT 5.0 is open to college teams from across India. We expect 500+ students to take part this edition. See the registration form for eligibility details specific to this edition.',
  },
  {
    q: 'How do I register?',
    a: 'Click "Register for ADAPPT" below to fill out the registration form on this site as a team, then pay the registration fee via UPI. Your registered email becomes your portal login identifier.',
  },
  {
    q: 'Can I change my domain after registering?',
    a: 'No. Your domain is fixed at the time of registration and cannot be changed from the portal.',
  },
  {
    q: 'What do I submit for Round 1?',
    a: 'Your pitch materials — a PPT/PDF and a video — uploaded through the participant portal before the submission deadline shown on your dashboard.',
  },
  {
    q: 'What happens after Round 1?',
    a: 'Shortlisted teams move to Round 2 — Tech Twists, where you’ll adapt your idea to new technical challenges and present an updated PPT. A working prototype is optional at this stage.',
  },
]

const DOMAIN_ICONS = {
  'cybersecurity-smart-homes': Lock,
  'ai-foodtech': UtensilsCrossed,
  'robotics-disaster-management': Bot,
}

const EVENT_DETAILS = [
  { icon: CalendarDays, label: 'Dates', value: 'Round 1 upto 17 Oct · Round 2: 23–24 Oct 2026' },
  { icon: MapPin, label: 'Venue', value: 'MPSTME, Mumbai' },
  { icon: Users, label: 'Team Size', value: '4 members per team' },
  { icon: Trophy, label: 'Expected Participants', value: '500+ students, colleges across India' },
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
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 grid-overlay" />
        <div className="pointer-events-none absolute -top-40 left-1/2 h-[560px] w-[560px] -translate-x-1/2 glow-accent" />

        <div className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6 sm:py-32">
          <div className="max-w-2xl animate-fade-in-up">
            <Badge variant="accent">ADAPPT 5.0 · Venture Sprint</Badge>
            <h1 className="mt-5 text-5xl font-extrabold leading-[1.05] tracking-tight text-ink-950 sm:text-6xl">
              BUILD WHAT'S
              <br />
              <span className="text-gradient-accent">NEXT.</span>
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-600">
              Develop an idea against a real-world problem, adapt it through live technical
              twists, and pitch it to experts — across two rounds that reward adaptability as
              much as the idea itself.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/register">
                <Button variant="accent" size="lg">
                  Register for ADAPPT <ArrowRight size={18} />
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="secondary" size="lg">
                  Portal Login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Event details strip */}
      <section className="border-t border-ink-100 bg-surface py-10">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
          {EVENT_DETAILS.map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-start gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-accent-600/30 bg-accent-600/10 text-accent-500">
                <Icon size={17} />
              </span>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</p>
                <p className="mt-0.5 text-sm font-medium text-ink-900">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* About */}
      <section id="about" className="py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">About ADAPPT 5.0</h2>
          <div className="mt-3 flex max-w-3xl flex-col gap-3 text-ink-600">
            <p>
              ADAPPT 5.0: Venture Sprint is an innovation-driven ideathon organized by IETE-SF
              MPSTME, designed to challenge participants to develop innovative solutions to
              real-world problems.
            </p>
            <p>
              The event follows a multi-stage format where participants begin by developing an
              idea based on a broad problem statement and progressively transform their idea
              through technical challenges and expert interactions.
            </p>
            <p>
              Unlike a conventional ideathon, ADAPPT 5.0 focuses on idea development,
              adaptability, technical problem-solving, and presentation — allowing participants to
              take their solutions through multiple stages of development.
            </p>
          </div>
        </div>
      </section>

      {/* Domains */}
      <section id="domains" className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Competition Domains</h2>
          <p className="mt-2 text-ink-600">Your domain is assigned based on your registration.</p>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {domains === null &&
              [0, 1, 2].map((i) => <Skeleton key={i} className="h-40 rounded-lg" />)}
            {domains?.length === 0 && (
              <p className="text-sm text-ink-500">Domains will be announced soon.</p>
            )}
            {domains?.map((d) => {
              const Icon = DOMAIN_ICONS[d.slug] || Lightbulb
              return (
                <Card key={d.id} interactive>
                  <CardBody className="flex flex-col gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-accent-600/30 bg-accent-600/10 text-accent-500">
                      <Icon size={20} />
                    </span>
                    <h3 className="font-semibold text-ink-900">{d.name}</h3>
                    <p className="text-sm leading-relaxed text-ink-500">
                      {d.description || 'Details coming soon.'}
                    </p>
                  </CardBody>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      {/* Event Format */}
      <section id="format" className="py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Event Format</h2>
          <p className="mt-2 max-w-2xl text-ink-600">
            ADAPPT 5.0 consists of two major rounds, followed by a final presentation and
            evaluation.
          </p>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <Card interactive>
              <CardBody className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent-600/30 bg-accent-600/10 text-accent-500">
                    <Video size={18} />
                  </span>
                  <h3 className="font-semibold text-ink-900">Round 1 — Idea Pitch</h3>
                </div>
                <p className="text-sm leading-relaxed text-ink-500">
                  Round 1 begins with the release of the domains to participants. Teams brainstorm
                  and develop an innovative idea addressing the given problem, presented as a{' '}
                  <strong className="text-ink-800">Video Pitch or PPT</strong>. The focus is on the
                  idea, its approach, and the proposed solution.
                </p>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-ink-500">
                  <Badge variant="neutral">Deadline: 17 Oct, 12:00 AM</Badge>
                  <Badge variant="neutral">Results: 19 Oct, 12:00 AM</Badge>
                </div>
              </CardBody>
            </Card>

            <Card interactive>
              <CardBody className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent-600/30 bg-accent-600/10 text-accent-500">
                    <Wrench size={18} />
                  </span>
                  <h3 className="font-semibold text-ink-900">Round 2 — Tech Twists</h3>
                </div>
                <p className="text-sm leading-relaxed text-ink-500">
                  Shortlisted teams receive technical twists / challenges they must incorporate
                  into their solution, then prepare a{' '}
                  <strong className="text-ink-800">PPT presenting their developed solution</strong>.
                  A working prototype is optional. This round tests the team's ability to adapt,
                  innovate, and solve technical challenges while keeping the core idea intact.
                </p>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-ink-500">
                  <Badge variant="neutral">For shortlisted teams</Badge>
                  <Badge variant="neutral">23–24 Oct 2026</Badge>
                </div>
              </CardBody>
            </Card>
          </div>

          <div className="mt-4 flex items-center gap-3 rounded-lg border border-ink-200 bg-surface px-5 py-4">
            <Trophy size={18} className="shrink-0 text-accent-500" />
            <p className="text-sm text-ink-600">
              Both rounds are followed by a final presentation and evaluation in front of judges
              at MPSTME, Mumbai.
            </p>
          </div>

          <div className="mt-4">
            <Card interactive>
              <CardBody className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-accent-600/30 bg-accent-600/10 text-accent-500">
                  <Lightbulb size={18} />
                </span>
                <div>
                  <h3 className="font-medium text-ink-900">Weekly Hints</h3>
                  <p className="text-sm text-ink-500">
                    Organizers publish guidance between rounds to help teams refine their idea and
                    stay on track.
                  </p>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>

      {/* Timeline / Submission info */}
      <section id="timeline" className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Timeline &amp; Submission</h2>
          <p className="mt-2 text-ink-600">
            Round 1 submissions are tracked live below; the portal enforces this deadline
            automatically.
          </p>
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
      <section className="py-16">
        <div className="mx-auto flex max-w-6xl items-start gap-4 px-4 sm:px-6">
          <ShieldCheck size={24} className="mt-1 shrink-0 text-accent-500" />
          <p className="text-sm text-ink-600">
            Portal access is only granted to the email address used at registration. If you
            haven't set up your portal account yet, use the <Link to="/login" className="font-medium text-accent-500 underline">Portal Login</Link> page
            to request an activation link.
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="border-t border-ink-100 bg-surface py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <h2 className="text-2xl font-semibold text-ink-950">Frequently Asked Questions</h2>
          <div className="mt-6 divide-y divide-ink-100 rounded-lg border border-ink-200 bg-paper">
            {FAQS.map((item) => (
              <details key={item.q} className="group px-5 py-4">
                <summary className="cursor-pointer list-none text-sm font-medium text-ink-900 marker:content-none">
                  <span className="flex items-center justify-between gap-3">
                    {item.q}
                    <span className="text-ink-400 transition-transform duration-200 group-open:rotate-45">+</span>
                  </span>
                </summary>
                <p className="mt-2 text-sm text-ink-500">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Register CTA */}
      <section id="register" className="py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="relative overflow-hidden rounded-2xl border border-accent-600/25 bg-gradient-to-br from-accent-600/15 via-transparent to-transparent px-6 py-10 sm:px-10">
            <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full glow-accent" />
            <div className="relative flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
              <div>
                <h2 className="text-2xl font-semibold text-ink-950">Ready to compete?</h2>
                <p className="mt-2 text-ink-500">
                  Register your team of 4 and pay the entry fee online.
                </p>
              </div>
              <Link to="/register">
                <Button variant="accent" size="lg">
                  Register for ADAPPT <ArrowRight size={18} />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
