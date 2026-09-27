import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, XCircle, Loader2, ArrowRight, ShieldCheck, MailCheck } from 'lucide-react'
import { Brand } from '../../components/Brand'
import { Button } from '../../components/ui/Button'
import { Card, CardBody } from '../../components/ui/Card'
import { Field, Input, Select } from '../../components/ui/Field'
import { FileDropzone } from '../../components/ui/FileDropzone'
import { PageLoader } from '../../components/ui/States'
import { publicApi, uploadsApi } from '../../services/team'
import { registrationApi } from '../../services/registration'
import { getErrorMessage } from '../../services/api'
import paymentQr from '../../assets/payment-qr.jpg'

const PAYMENT_SCREENSHOT_ACCEPT = '.jpg,.jpeg,.png,.webp,.pdf'
const PAYMENT_SCREENSHOT_ALLOWED = ['jpg', 'jpeg', 'png', 'webp', 'pdf']
const PAYMENT_SCREENSHOT_MAX_MB = 10

const TEAM_SIZES = [1, 2, 3, 4]

const emptyForm = {
  full_name: '',
  mobile_number: '',
  email: '',
  college_name: '',
  degree_course: '',
  team_name: '',
  domain_slug: '',
  team_size: 1,
  members: [],
}

export function RegisterPage() {
  const [domains, setDomains] = useState(null)
  const [paymentPerPerson, setPaymentPerPerson] = useState(300)
  const [form, setForm] = useState(emptyForm)
  const [errors, setErrors] = useState({})
  const [teamNameStatus, setTeamNameStatus] = useState('idle') // idle | checking | available | taken
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [result, setResult] = useState(null)
  const teamNameCheckRef = useRef(0)

  useEffect(() => {
    publicApi.getDomains().then(({ data }) => setDomains(data))
    publicApi.getTimeline().then(({ data }) => setPaymentPerPerson(data.payment_per_person_inr))
  }, [])

  const updateField = (field, value) => setForm((prev) => ({ ...prev, [field]: value }))

  const updateTeamSize = (size) => {
    setForm((prev) => {
      const members = Array.from({ length: size - 1 }, (_, i) => prev.members[i] || { name: '', phone: '' })
      return { ...prev, team_size: size, members }
    })
  }

  const updateMember = (index, field, value) => {
    setForm((prev) => {
      const members = [...prev.members]
      members[index] = { ...members[index], [field]: value }
      return { ...prev, members }
    })
  }

  const checkTeamName = async (name) => {
    if (!name.trim()) {
      setTeamNameStatus('idle')
      return
    }
    const requestId = ++teamNameCheckRef.current
    setTeamNameStatus('checking')
    try {
      const { data } = await registrationApi.checkTeamName(name.trim())
      if (requestId !== teamNameCheckRef.current) return
      setTeamNameStatus(data.available ? 'available' : 'taken')
    } catch {
      if (requestId === teamNameCheckRef.current) setTeamNameStatus('idle')
    }
  }

  const validate = () => {
    const next = {}
    if (!form.full_name.trim()) next.full_name = 'Required'
    if (!/^[0-9+\s-]{7,15}$/.test(form.mobile_number.trim())) next.mobile_number = 'Enter a valid mobile number'
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) next.email = 'Enter a valid email'
    if (!form.college_name.trim()) next.college_name = 'Required'
    if (!form.degree_course.trim()) next.degree_course = 'Required'
    if (!form.team_name.trim()) next.team_name = 'Required'
    else if (teamNameStatus === 'taken') next.team_name = 'This team name is already taken'
    if (!form.domain_slug) next.domain_slug = 'Choose a domain'
    form.members.forEach((m, i) => {
      if (!m.name.trim()) next[`member_${i}_name`] = 'Required'
      if (!/^[0-9+\s-]{7,15}$/.test(m.phone.trim())) next[`member_${i}_phone`] = 'Enter a valid phone number'
    })
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitError('')
    if (!validate()) return

    setSubmitting(true)
    try {
      const { data } = await registrationApi.submit(form)
      setResult(data)
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Could not submit your registration. Please try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  if (domains === null) return <PageLoader />

  if (result) {
    return <PaymentStep result={result} paymentPerPerson={paymentPerPerson} email={form.email.trim().toLowerCase()} />
  }

  return (
    <div className="min-h-screen bg-paper px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>

        <Card>
          <CardBody className="p-6 sm:p-8">
            <h1 className="text-xl font-semibold text-ink-950">Register for ADAPPT</h1>
            <p className="mt-1 text-sm text-ink-500">
              Fill in your team's details below. You'll pay the registration fee via UPI in the
              next step.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Full Name" error={errors.full_name}>
                  <Input
                    value={form.full_name}
                    onChange={(e) => updateField('full_name', e.target.value)}
                    placeholder="Your full name"
                  />
                </Field>
                <Field label="Mobile Number" error={errors.mobile_number}>
                  <Input
                    value={form.mobile_number}
                    onChange={(e) => updateField('mobile_number', e.target.value)}
                    placeholder="10-digit mobile number"
                  />
                </Field>
              </div>

              <Field label="Email ID" error={errors.email}>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => updateField('email', e.target.value)}
                  placeholder="you@example.com"
                />
              </Field>

              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="College Name" error={errors.college_name}>
                  <Input
                    value={form.college_name}
                    onChange={(e) => updateField('college_name', e.target.value)}
                  />
                </Field>
                <Field label="Degree / Course" error={errors.degree_course}>
                  <Input
                    value={form.degree_course}
                    onChange={(e) => updateField('degree_course', e.target.value)}
                    placeholder="e.g. B.Tech Computer Science"
                  />
                </Field>
              </div>

              <Field label="Team Name" error={errors.team_name} hint="This must be unique across all teams.">
                <div className="relative">
                  <Input
                    value={form.team_name}
                    onChange={(e) => {
                      updateField('team_name', e.target.value)
                      setTeamNameStatus('idle')
                    }}
                    onBlur={(e) => checkTeamName(e.target.value)}
                    className="pr-9"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2">
                    {teamNameStatus === 'checking' && <Loader2 size={16} className="animate-spin text-ink-400" />}
                    {teamNameStatus === 'available' && <CheckCircle2 size={16} className="text-success-600" />}
                    {teamNameStatus === 'taken' && <XCircle size={16} className="text-danger-600" />}
                  </span>
                </div>
                {teamNameStatus === 'available' && !errors.team_name && (
                  <p className="text-xs text-success-600">This team name is available.</p>
                )}
              </Field>

              <Field label="Choose Your Domain" error={errors.domain_slug}>
                <Select value={form.domain_slug} onChange={(e) => updateField('domain_slug', e.target.value)}>
                  <option value="">Select a domain</option>
                  {domains.map((d) => (
                    <option key={d.slug} value={d.slug}>
                      {d.name}
                    </option>
                  ))}
                </Select>
              </Field>

              <Field label="Number of Members in Team">
                <div className="flex gap-2" role="radiogroup" aria-label="Team size">
                  {TEAM_SIZES.map((size) => (
                    <button
                      key={size}
                      type="button"
                      role="radio"
                      aria-checked={form.team_size === size}
                      onClick={() => updateTeamSize(size)}
                      className={`h-10 w-12 rounded-md border text-sm font-medium transition-colors ${
                        form.team_size === size
                          ? 'border-accent-600 bg-accent-600 text-white'
                          : 'border-ink-300 bg-transparent text-ink-800 hover:border-accent-400 hover:text-ink-950'
                      }`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </Field>

              {form.members.map((member, i) => (
                <div key={i} className="grid gap-4 rounded-md border border-ink-100 bg-ink-50 p-4 sm:grid-cols-2">
                  <Field label={`Member ${i + 2} Name`} error={errors[`member_${i}_name`]}>
                    <Input
                      value={member.name}
                      onChange={(e) => updateMember(i, 'name', e.target.value)}
                    />
                  </Field>
                  <Field label={`Member ${i + 2} Phone Number`} error={errors[`member_${i}_phone`]}>
                    <Input
                      value={member.phone}
                      onChange={(e) => updateMember(i, 'phone', e.target.value)}
                    />
                  </Field>
                </div>
              ))}

              <div className="rounded-md border border-ink-100 bg-ink-50 px-4 py-3 text-sm text-ink-700">
                Registration fee: <strong>₹{paymentPerPerson} per person</strong> — total due for a
                team of {form.team_size}: <strong>₹{form.team_size * paymentPerPerson}</strong>
              </div>

              {submitError && <p className="text-sm text-danger-600">{submitError}</p>}

              <Button type="submit" variant="accent" size="lg" loading={submitting} className="w-full">
                Continue to Payment <ArrowRight size={16} />
              </Button>
            </form>
          </CardBody>
        </Card>

        <p className="mt-4 text-center text-sm text-ink-500">
          Already registered? <Link to="/login" className="font-medium text-accent-700 hover:underline">Portal Login</Link>
        </p>
      </div>
    </div>
  )
}

const emptyScreenshotSlot = { file: null, status: 'idle', progress: 0, error: '', meta: null }

function PaymentStep({ result, paymentPerPerson, email }) {
  const [screenshot, setScreenshot] = useState(emptyScreenshotSlot)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const uploadScreenshot = async (file) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!PAYMENT_SCREENSHOT_ALLOWED.includes(ext)) {
      setScreenshot({
        file,
        status: 'error',
        progress: 0,
        error: `This file type is not supported. Allowed: ${PAYMENT_SCREENSHOT_ALLOWED.join(', ')}.`,
        meta: null,
      })
      return
    }
    if (file.size > PAYMENT_SCREENSHOT_MAX_MB * 1024 * 1024) {
      setScreenshot({
        file,
        status: 'error',
        progress: 0,
        error: `The selected file exceeds the allowed size of ${PAYMENT_SCREENSHOT_MAX_MB}MB.`,
        meta: null,
      })
      return
    }

    setScreenshot({ file, status: 'uploading', progress: 0, error: '', meta: null })
    try {
      const { data: presign } = await registrationApi.presignPaymentScreenshot(
        result.registration_id,
        email,
        file
      )
      await uploadsApi.uploadToUrl(presign.upload_url, file, (pct) =>
        setScreenshot((prev) => ({ ...prev, progress: pct }))
      )
      setScreenshot({
        file,
        status: 'done',
        progress: 100,
        error: '',
        meta: {
          storage_key: presign.storage_key,
          original_filename: file.name,
          content_type: file.type || 'application/octet-stream',
          file_size_bytes: file.size,
        },
      })
    } catch (err) {
      setScreenshot({ file, status: 'error', progress: 0, error: getErrorMessage(err, 'Upload failed.'), meta: null })
    }
  }

  const handleSubmitProof = async () => {
    setSubmitError('')
    setSubmitting(true)
    try {
      await registrationApi.confirmPaymentScreenshot(result.registration_id, email, screenshot.meta)
      setSubmitted(true)
    } catch (err) {
      setSubmitError(getErrorMessage(err, 'Could not submit your payment screenshot. Please try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-paper px-4 py-10">
        <div className="mx-auto max-w-md">
          <div className="mb-8 flex justify-center">
            <Brand />
          </div>
          <Card>
            <CardBody className="flex flex-col items-center gap-3 p-6 text-center sm:p-8">
              <MailCheck size={32} className="text-success-600" />
              <h1 className="text-xl font-semibold text-ink-950">Payment proof received</h1>
              <p className="text-sm text-ink-500">
                Our team will verify your payment for <strong className="text-ink-800">{result.team_name}</strong>.
                You'll receive an email with your portal login credentials by the end of the day
                once it's confirmed.
              </p>
              <Link to="/" className="mt-2 text-sm font-medium text-accent-700 hover:underline">
                Back to Home
              </Link>
            </CardBody>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-paper px-4 py-10">
      <div className="mx-auto max-w-md">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>

        <Card>
          <CardBody className="flex flex-col items-center gap-4 p-6 text-center sm:p-8">
            <CheckCircle2 size={32} className="text-success-600" />
            <div>
              <h1 className="text-xl font-semibold text-ink-950">Registration received</h1>
              <p className="mt-1 text-sm text-ink-500">
                Team <strong className="text-ink-800">{result.team_name}</strong> — {result.team_size}{' '}
                member{result.team_size > 1 ? 's' : ''}
              </p>
            </div>

            <img
              src={paymentQr}
              alt="Payment QR code"
              className="h-56 w-56 rounded-lg bg-white object-contain p-2"
            />

            <div className="w-full rounded-md border border-accent-100 bg-accent-50 px-4 py-3">
              <p className="text-sm text-neutral-700">Scan the QR code and pay via UPI.</p>
              <p className="mt-2 text-lg font-semibold text-accent-700">
                ₹{result.payment_amount_inr} due (₹{paymentPerPerson} × {result.team_size})
              </p>
            </div>

            <div className="w-full text-left">
              <FileDropzone
                label="Upload Payment Screenshot"
                hint={`Allowed: ${PAYMENT_SCREENSHOT_ALLOWED.join(', ')} · Max ${PAYMENT_SCREENSHOT_MAX_MB}MB`}
                accept={PAYMENT_SCREENSHOT_ACCEPT}
                file={screenshot.file}
                status={screenshot.status}
                progress={screenshot.progress}
                errorMessage={screenshot.error}
                onSelect={uploadScreenshot}
                onRetry={() => screenshot.file && uploadScreenshot(screenshot.file)}
              />
            </div>

            {submitError && <p className="text-sm text-danger-600">{submitError}</p>}

            <Button
              variant="accent"
              size="lg"
              className="w-full"
              disabled={screenshot.status !== 'done'}
              loading={submitting}
              onClick={handleSubmitProof}
            >
              Submit Payment Proof <ArrowRight size={16} />
            </Button>

            <div className="flex items-start gap-2 text-left text-xs text-ink-500">
              <ShieldCheck size={16} className="mt-0.5 shrink-0 text-ink-400" />
              <p>
                Your registration isn't complete until your payment is verified — you won't be
                able to log in to the portal until then.
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
