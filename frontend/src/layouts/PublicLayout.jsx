import { Link, Outlet } from 'react-router-dom'
import { Brand } from '../components/Brand'

const NAV_LINKS = [
  { label: 'About', href: '#about' },
  { label: 'Domains', href: '#domains' },
  { label: 'Timeline', href: '#timeline' },
  { label: 'FAQ', href: '#faq' },
]

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="sticky top-0 z-40 border-b border-ink-100 bg-paper/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Brand />
          <nav className="hidden items-center gap-6 md:flex">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="text-sm text-ink-600 hover:text-ink-900">
                {link.label}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium text-ink-700 hover:text-ink-900">
              Portal Login
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-ink-100 bg-surface">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-ink-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <Brand />
          <p>© 2026 ADAPPT · Organized by [ORGANIZING COMMITTEE]</p>
        </div>
      </footer>
    </div>
  )
}
