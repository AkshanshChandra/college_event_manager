import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  ClipboardList,
  Users,
  Layers,
  FileText,
  Lightbulb,
  UploadCloud,
  SlidersHorizontal,
  ScrollText,
  LogOut,
  Menu,
} from 'lucide-react'
import { Brand } from '../components/Brand'
import { Badge } from '../components/ui/Badge'
import { useAuth } from '../hooks/useAuth'

const NAV_ITEMS = [
  { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admin/registrations', label: 'Registrations', icon: ClipboardList },
  { to: '/admin/teams', label: 'Teams', icon: Users },
  { to: '/admin/domains', label: 'Domains', icon: Layers },
  { to: '/admin/problem-statements', label: 'Problem Statements', icon: FileText },
  { to: '/admin/hints', label: 'Hints', icon: Lightbulb },
  { to: '/admin/submissions', label: 'Submissions', icon: UploadCloud },
  { to: '/admin/settings', label: 'Competition Settings', icon: SlidersHorizontal },
  { to: '/admin/audit-logs', label: 'Audit Logs', icon: ScrollText },
]

export function AdminLayout() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)

  const navContent = (
    <>
      <div className="flex items-center gap-2 px-4 pb-4 pt-5">
        <Brand />
        <Badge variant="neutral">Admin</Badge>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto px-2">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? 'bg-accent-600 text-white' : 'text-ink-500 hover:bg-ink-100 hover:text-ink-950'
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-ink-100 px-4 py-4">
        <p className="truncate text-xs text-ink-500">{user?.email}</p>
        <button
          onClick={logout}
          className="mt-2 flex items-center gap-2 text-sm font-medium text-ink-600 hover:text-danger-600"
        >
          <LogOut size={16} /> Logout
        </button>
      </div>
    </>
  )

  return (
    <div className="flex min-h-screen bg-paper">
      <aside className="hidden w-64 flex-col border-r border-ink-100 bg-surface md:flex">
        {navContent}
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="relative flex w-64 flex-col bg-surface">{navContent}</aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-ink-100 bg-surface px-4 md:hidden">
          <Brand />
          <button onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>
        </header>
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
