import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'
import { Brand } from '../../components/Brand'
import { Button } from '../../components/ui/Button'
import { Field, Input } from '../../components/ui/Field'
import { useAuth } from '../../hooks/useAuth'
import { getErrorMessage } from '../../services/api'

export function AdminLoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
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
      navigate('/admin/dashboard', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'Incorrect email or password.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-950 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Brand className="text-white [&_span:last-child]:text-white" />
        </div>
        <div className="rounded-lg border border-ink-800 bg-ink-900 p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-accent-400" />
            <h1 className="text-lg font-semibold text-white">Admin Login</h1>
          </div>
          <p className="mt-1 text-sm text-ink-400">Organizer access only.</p>

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <Field label={<span className="text-ink-200">Email</span>}>
              <Input
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@adappt.dev"
              />
            </Field>
            <Field label={<span className="text-ink-200">Password</span>}>
              <Input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>
            {error && <p className="text-sm text-danger-600">{error}</p>}
            <Button type="submit" variant="accent" loading={loading} className="mt-1 w-full">
              Log In
            </Button>
          </form>
        </div>
        <p className="mt-4 text-center text-sm text-ink-400">
          <Link to="/login" className="hover:underline">Participant login</Link>
        </p>
      </div>
    </div>
  )
}
