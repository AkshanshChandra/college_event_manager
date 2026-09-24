import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MailCheck } from 'lucide-react'
import { Brand } from '../../components/Brand'
import { Button } from '../../components/ui/Button'
import { Field, Input } from '../../components/ui/Field'
import { authApi } from '../../services/auth'
import { getErrorMessage } from '../../services/api'

export function RequestAccessPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authApi.requestAccess(email)
      setSent(true)
    } catch (err) {
      setError(
        getErrorMessage(err, 'We could not find this email in the ADAPPT registration records.')
      )
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
          {sent ? (
            <div className="flex flex-col items-center gap-2 py-4 text-center">
              <MailCheck size={28} className="text-accent-600" />
              <h1 className="text-lg font-semibold text-ink-950">Check your email</h1>
              <p className="text-sm text-ink-500">
                If <span className="font-medium text-ink-800">{email}</span> is registered for
                ADAPPT, an activation link has been sent to it.
              </p>
              <Link to="/login" className="mt-3 text-sm font-medium text-accent-700 hover:underline">
                Back to login
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-ink-950">Activate Portal Access</h1>
              <p className="mt-1 text-sm text-ink-500">
                Enter the email you used to register your team on the ADAPPT form.
              </p>
              <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
                <Field label="Registered Email">
                  <Input
                    type="email"
                    required
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="team-leader@example.com"
                  />
                </Field>
                {error && <p className="text-sm text-danger-600">{error}</p>}
                <Button type="submit" loading={loading} className="w-full">
                  Send Activation Link
                </Button>
              </form>
              <p className="mt-5 text-center text-sm text-ink-500">
                Already activated? <Link to="/login" className="font-medium text-accent-700 hover:underline">Log in</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
