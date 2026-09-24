import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LogIn } from 'lucide-react'
import { Brand } from '../../components/Brand'
import { Button } from '../../components/ui/Button'
import { Field, Input } from '../../components/ui/Field'
import { useAuth } from '../../hooks/useAuth'
import { getErrorMessage } from '../../services/api'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate(location.state?.from?.pathname || '/dashboard', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'Incorrect email or password.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>
        <div className="rounded-lg border border-ink-200 bg-surface p-6 shadow-sm">
          <h1 className="text-lg font-semibold text-ink-950">Participant Login</h1>
          <p className="mt-1 text-sm text-ink-500">Sign in with your registered team email.</p>

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <Field label="Email">
              <Input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>
            {error && <p className="text-sm text-danger-600">{error}</p>}
            <Button type="submit" loading={loading} className="mt-1 w-full">
              <LogIn size={16} /> Log In
            </Button>
          </form>

          <p className="mt-5 text-center text-sm text-ink-500">
            Don't have portal access yet?{' '}
            <Link to="/request-access" className="font-medium text-accent-700 hover:underline">
              Activate your account
            </Link>
          </p>
        </div>
        <p className="mt-4 text-center text-sm text-ink-400">
          Organizer? <Link to="/admin/login" className="hover:underline">Admin login</Link>
        </p>
      </div>
    </div>
  )
}
