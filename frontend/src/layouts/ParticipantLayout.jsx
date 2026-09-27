import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Lightbulb,
  UploadCloud,
  Users,
  LogOut,
  Menu,
} from 'lucide-react'
import { Brand } from '../components/Brand'
import { Badge } from '../components/ui/Badge'
import { useAuth } from '../hooks/useAuth'
import { teamApi } from '../services/team'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/problem-statement', label: 'Problem Statement', icon: FileText },
  { to: '/hints', label: 'Weekly Hints', icon: Lightbulb },
  { to: '/submission', label: 'Submission', icon: UploadCloud },
  { to: '/team', label: 'Team', icon: Users },
]

export function ParticipantLayout() {
  const { user, logout } = useAuth()
  const [team, setTeam] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    teamApi
      .getTeam()
      .then(({ data }) => setTeam(data))
      .catch(() => setTeam(null))
  }, [])

  const navContent = (
    <>
      <div className="px-4 pb-4 pt-5">
        <Brand />
      </div>
      {team && (
        <div className="mx-4 mb-4 rounded-md border border-ink-100 bg-ink-50 px-3 py-2.5">
          <p className="truncate text-sm font-medium text-ink-900">{team.name}</p>
          <Badge variant="accent" className="mt-1.5">
            {team.domain.name}
          </Badge>
        </div>
      )}
      <nav className="flex flex-1 flex-col gap-0.5 px-2">
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
          <Outlet context={{ team }} />
        </main>
      </div>
    </div>
  )
}
