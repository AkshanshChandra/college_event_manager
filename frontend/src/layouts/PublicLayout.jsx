import { Link, Outlet } from 'react-router-dom'
import { Brand } from '../components/Brand'
import ietesfLogo from '../assets/brand/ietesf-logo.png'
import ieteLogo from '../assets/brand/iete-logo.png'

const NAV_LINKS = [
  { label: 'About', href: '#about' },
  { label: 'Domains', href: '#domains' },
  { label: 'Timeline', href: '#timeline' },
  { label: 'FAQ', href: '#faq' },
]

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <div className="h-[3px] w-full bg-gradient-to-r from-transparent via-accent-600 to-transparent" />
      <header className="sticky top-0 z-40 border-b border-ink-100 bg-paper/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Brand />
          <nav className="hidden items-center gap-6 md:flex">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="text-sm text-ink-600 hover:text-ink-950">
                {link.label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-ink-700 hover:text-ink-950">
              Portal Login
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-ink-100 bg-surface">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 border-b border-ink-100 px-4 py-8 sm:px-6">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-500">
            Organized in association with
          </p>
          <div className="flex items-center gap-8">
            <img src={ietesfLogo} alt="IETE Student Forum, MPSTME" className="h-14 w-auto" />
            <img src={ieteLogo} alt="The Institution of Electronics and Telecommunication Engineers" className="h-14 w-auto" />
          </div>
        </div>
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-6 text-sm text-ink-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <Brand />
          <p>© 2026 ADAPPT · Organized by IETE Student Forum, MPSTME</p>
        </div>
      </footer>
    </div>
  )
}
