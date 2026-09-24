import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Brand } from '../../components/Brand'
import { Button } from '../../components/ui/Button'
import { Field, Input } from '../../components/ui/Field'
import { useAuth } from '../../hooks/useAuth'
import { getErrorMessage } from '../../services/api'

export function ActivatePage() {
  const { token } = useParams()
  const { activate } = useAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await activate(token, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'This activation link is invalid or has expired.'))
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
          <h1 className="text-lg font-semibold text-ink-950">Set Your Password</h1>
          <p className="mt-1 text-sm text-ink-500">
            Choose a password to finish activating your ADAPPT portal account.
          </p>
          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <Field label="New Password" hint="At least 8 characters.">
              <Input
                type="password"
                required
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <Field label="Confirm Password">
              <Input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </Field>
            {error && <p className="text-sm text-danger-600">{error}</p>}
            <Button type="submit" loading={loading} className="w-full">
              Activate Account
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
