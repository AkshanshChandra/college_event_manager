import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import { RequireParticipant, RequireAdmin } from './components/RouteGuards'

import { PublicLayout } from './layouts/PublicLayout'
import { ParticipantLayout } from './layouts/ParticipantLayout'
import { AdminLayout } from './layouts/AdminLayout'

import { LandingPage } from './pages/public/LandingPage'
import { LoginPage } from './pages/public/LoginPage'
import { AdminLoginPage } from './pages/public/AdminLoginPage'
import { RequestAccessPage } from './pages/public/RequestAccessPage'
import { ActivatePage } from './pages/public/ActivatePage'
import { RegisterPage } from './pages/public/RegisterPage'

import { DashboardPage } from './pages/participant/DashboardPage'
import { ProblemStatementPage } from './pages/participant/ProblemStatementPage'
import { HintsPage } from './pages/participant/HintsPage'
import { SubmissionPage } from './pages/participant/SubmissionPage'
import { TeamPage } from './pages/participant/TeamPage'

import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { AdminRegistrationsPage } from './pages/admin/AdminRegistrationsPage'
import { AdminTeamsPage } from './pages/admin/AdminTeamsPage'
import { AdminTeamDetailPage } from './pages/admin/AdminTeamDetailPage'
import { AdminDomainsPage } from './pages/admin/AdminDomainsPage'
import { AdminProblemStatementsPage } from './pages/admin/AdminProblemStatementsPage'
import { AdminHintsPage } from './pages/admin/AdminHintsPage'
import { AdminSubmissionsPage } from './pages/admin/AdminSubmissionsPage'
import { AdminSettingsPage } from './pages/admin/AdminSettingsPage'
import { AdminAuditLogsPage } from './pages/admin/AdminAuditLogsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public */}
            <Route element={<PublicLayout />}>
              <Route path="/" element={<LandingPage />} />
            </Route>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/admin/login" element={<AdminLoginPage />} />
            <Route path="/request-access" element={<RequestAccessPage />} />
            <Route path="/activate/:token" element={<ActivatePage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Participant */}
            <Route element={<RequireParticipant />}>
              <Route element={<ParticipantLayout />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/problem-statement" element={<ProblemStatementPage />} />
                <Route path="/hints" element={<HintsPage />} />
                <Route path="/submission" element={<SubmissionPage />} />
                <Route path="/team" element={<TeamPage />} />
              </Route>
            </Route>

            {/* Admin */}
            <Route element={<RequireAdmin />}>
              <Route element={<AdminLayout />}>
                <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
                <Route path="/admin/registrations" element={<AdminRegistrationsPage />} />
                <Route path="/admin/teams" element={<AdminTeamsPage />} />
                <Route path="/admin/teams/:teamId" element={<AdminTeamDetailPage />} />
                <Route path="/admin/domains" element={<AdminDomainsPage />} />
                <Route path="/admin/problem-statements" element={<AdminProblemStatementsPage />} />
                <Route path="/admin/hints" element={<AdminHintsPage />} />
                <Route path="/admin/submissions" element={<AdminSubmissionsPage />} />
                <Route path="/admin/settings" element={<AdminSettingsPage />} />
                <Route path="/admin/audit-logs" element={<AdminAuditLogsPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
