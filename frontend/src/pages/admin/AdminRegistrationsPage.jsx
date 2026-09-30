import { useEffect, useState } from 'react'
import { Search, Download, Image as ImageIcon, Pencil, Mail } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Input, Select, Field } from '../../components/ui/Field'
import { Table, Td } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { Dialog } from '../../components/ui/Dialog'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { ACCOUNT_STATUS_META, PAYMENT_STATUS_META, formatDateTime } from '../../utils/status'

const PAGE_SIZE = 25

export function AdminRegistrationsPage() {
  const { notify } = useToast()
  const [rows, setRows] = useState(null)
  const [search, setSearch] = useState('')
  const [domain, setDomain] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [domains, setDomains] = useState([])
  const [page, setPage] = useState(1)
  const [updatingId, setUpdatingId] = useState(null)
  const [resendingId, setResendingId] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [editing, setEditing] = useState(null) // registration row being edited, or null

  useEffect(() => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
  }, [])

  const load = () => {
    setRows(null)
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (domain) params.domain = domain
    if (paymentMethod) params.payment_method = paymentMethod
    adminApi.listRegistrations(params).then(({ data }) => setRows(data))
  }

  useEffect(load, [search, domain, paymentMethod, page])

  const handleExportCsv = async () => {
    setExporting(true)
    try {
      const { data: blob } = await adminApi.exportRegistrationsCsv()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'adappt_registrations.csv'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      notify(getErrorMessage(err, 'Could not export registrations.'), 'error')
    } finally {
      setExporting(false)
    }
  }

  const setPaymentStatus = async (registration, next) => {
    setUpdatingId(registration.id)
    try {
      await adminApi.updatePaymentStatus(registration.id, next)
      notify(
        next === 'paid'
          ? "Marked as paid — credentials email sent to the team's leader."
          : 'Payment status updated.',
        'success'
      )
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not update payment status.'), 'error')
    } finally {
      setUpdatingId(null)
    }
  }

  const handleResendEmail = async (registration) => {
    setResendingId(registration.id)
    try {
      await adminApi.resendRegistrationEmail(registration.id)
      notify('Activation email re-sent to the team leader.', 'success')
    } catch (err) {
      notify(getErrorMessage(err, 'Could not resend the email.'), 'error')
    } finally {
      setResendingId(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Registrations"
        description="Teams registered through the portal's registration form."
        action={
          <Button variant="secondary" loading={exporting} onClick={handleExportCsv}>
            <Download size={16} /> Export CSV
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative w-full max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <Input
            className="pl-9"
            placeholder="Search team, leader, email…"
            value={search}
            onChange={(e) => {
              setPage(1)
              setSearch(e.target.value)
            }}
          />
        </div>
        <Select
          className="w-48"
          value={domain}
          onChange={(e) => {
            setPage(1)
            setDomain(e.target.value)
          }}
        >
          <option value="">All Domains</option>
          {domains.map((d) => (
            <option key={d.slug} value={d.slug}>
              {d.name}
            </option>
          ))}
        </Select>
        <Select
          className="w-44"
          value={paymentMethod}
          onChange={(e) => {
            setPage(1)
            setPaymentMethod(e.target.value)
          }}
        >
          <option value="">All Payment Methods</option>
          <option value="online">Online</option>
          <option value="cash">Cash</option>
        </Select>
      </div>

      {rows === null ? (
        <PageLoader />
      ) : rows.length === 0 ? (
        <EmptyState title="No registrations found" description="Try a different search or filter." />
      ) : (
        <Table columns={['Team', 'Leader', 'Email', 'College', 'Domain', 'Size', 'Payment', 'Registered', 'Account', '']}>
          {rows.map((r) => (
            <tr key={r.id}>
              <Td className="font-medium text-ink-900">{r.team_name}</Td>
              <Td>{r.leader_name}</Td>
              <Td>{r.leader_email}</Td>
              <Td>{r.college}</Td>
              <Td>
                <Badge variant="neutral">{r.domain_slug}</Badge>
              </Td>
              <Td>{r.team_size ?? '—'}</Td>
              <Td>
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-1.5">
                    <StatusBadge meta={PAYMENT_STATUS_META[r.payment_status]} />
                    <Badge variant="neutral">{r.payment_method === 'cash' ? 'Cash' : 'Online'}</Badge>
                    {r.payment_amount_inr != null && (
                      <span className="text-xs text-ink-400">₹{r.payment_amount_inr}</span>
                    )}
                  </div>
                  {r.payment_screenshot_url && (
                    <a
                      href={r.payment_screenshot_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex w-fit items-center gap-1 text-xs font-medium text-accent-700 hover:underline"
                    >
                      <ImageIcon size={12} /> View Screenshot
                    </a>
                  )}
                </div>
              </Td>
              <Td>{formatDateTime(r.registered_at)}</Td>
              <Td>
                <StatusBadge meta={ACCOUNT_STATUS_META[r.account_status]} />
              </Td>
              <Td>
                <div className="flex flex-wrap gap-2">
                  {r.payment_status !== 'paid' && (
                    <Button
                      variant={r.payment_status === 'submitted' ? 'accent' : 'secondary'}
                      size="sm"
                      loading={updatingId === r.id}
                      onClick={() => setPaymentStatus(r, 'paid')}
                    >
                      Verify &amp; Send Credentials
                    </Button>
                  )}
                  {r.payment_status === 'paid' && (
                    <>
                      <Button
                        variant="secondary"
                        size="sm"
                        loading={updatingId === r.id}
                        onClick={() => setPaymentStatus(r, 'pending')}
                      >
                        Revert to Pending
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        loading={resendingId === r.id}
                        onClick={() => handleResendEmail(r)}
                      >
                        <Mail size={14} /> Resend Email
                      </Button>
                    </>
                  )}
                  <Button variant="secondary" size="sm" onClick={() => setEditing(r)}>
                    <Pencil size={14} /> Edit
                  </Button>
                </div>
              </Td>
            </tr>
          ))}
        </Table>
      )}

      {rows && rows.length > 0 && (
        <div className="mt-4 flex items-center justify-between text-sm text-ink-500">
          <span>Page {page}</span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={rows.length < PAGE_SIZE}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {editing && (
        <EditRegistrationDialog
          registration={editing}
          domains={domains}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
        />
      )}
    </div>
  )
}

function EditRegistrationDialog({ registration, domains, onClose, onSaved }) {
  const { notify } = useToast()
  const [form, setForm] = useState({
    team_name: registration.team_name,
    leader_name: registration.leader_name,
    leader_email: registration.leader_email,
    leader_phone: registration.leader_phone,
    college: registration.college,
    degree_course: registration.degree_course || '',
    domain_slug: registration.domain_slug,
    team_size: registration.team_size || 1,
    members: registration.members.map((m) => ({ name: m.name, phone: m.phone })),
  })
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)

  const digitsOnly = (value) => value.replace(/\D/g, '').slice(0, 10)

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

  const validate = () => {
    const next = {}
    if (!form.team_name.trim()) next.team_name = 'Required'
    if (!form.leader_name.trim()) next.leader_name = 'Required'
    if (!/^\S+@\S+\.\S+$/.test(form.leader_email.trim())) next.leader_email = 'Enter a valid email'
    if (!/^[0-9]{10}$/.test(form.leader_phone.trim())) next.leader_phone = 'Enter a valid 10-digit number'
    if (!form.college.trim()) next.college = 'Required'
    if (!form.degree_course.trim()) next.degree_course = 'Required'
    if (!form.domain_slug) next.domain_slug = 'Choose a domain'
    form.members.forEach((m, i) => {
      if (!m.name.trim()) next[`member_${i}_name`] = 'Required'
      if (!/^[0-9]{10}$/.test(m.phone.trim())) next[`member_${i}_phone`] = 'Enter a valid 10-digit number'
    })
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSave = async () => {
    if (!validate()) return
    setSaving(true)
    try {
      await adminApi.updateRegistration(registration.id, form)
      notify('Registration details updated.', 'success')
      onSaved()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save changes.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog
      open
      onClose={onClose}
      title="Edit Registration"
      description={`Team ${registration.team_name}`}
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave} loading={saving}>
            Save Changes
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Leader Name" error={errors.leader_name}>
            <Input value={form.leader_name} onChange={(e) => updateField('leader_name', e.target.value)} />
          </Field>
          <Field label="Leader Phone" error={errors.leader_phone}>
            <Input
              value={form.leader_phone}
              onChange={(e) => updateField('leader_phone', digitsOnly(e.target.value))}
              inputMode="numeric"
              maxLength={10}
            />
          </Field>
        </div>

        <Field label="Leader Email" error={errors.leader_email} hint="Fixing a typo here lets you resend the activation email to the corrected address.">
          <Input type="email" value={form.leader_email} onChange={(e) => updateField('leader_email', e.target.value)} />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="College" error={errors.college}>
            <Input value={form.college} onChange={(e) => updateField('college', e.target.value)} />
          </Field>
          <Field label="Degree / Course" error={errors.degree_course}>
            <Input value={form.degree_course} onChange={(e) => updateField('degree_course', e.target.value)} />
          </Field>
        </div>

        <Field label="Team Name" error={errors.team_name}>
          <Input value={form.team_name} onChange={(e) => updateField('team_name', e.target.value)} />
        </Field>

        <Field label="Domain" error={errors.domain_slug}>
          <Select value={form.domain_slug} onChange={(e) => updateField('domain_slug', e.target.value)}>
            {domains.map((d) => (
              <option key={d.slug} value={d.slug}>
                {d.name}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Team Size">
          <div className="flex gap-2" role="radiogroup" aria-label="Team size">
            {[1, 2, 3, 4].map((size) => (
              <button
                key={size}
                type="button"
                role="radio"
                aria-checked={form.team_size === size}
                onClick={() => updateTeamSize(size)}
                className={`h-9 w-11 rounded-md border text-sm font-medium transition-colors ${
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
              <Input value={member.name} onChange={(e) => updateMember(i, 'name', e.target.value)} />
            </Field>
            <Field label={`Member ${i + 2} Phone`} error={errors[`member_${i}_phone`]}>
              <Input
                value={member.phone}
                onChange={(e) => updateMember(i, 'phone', digitsOnly(e.target.value))}
                inputMode="numeric"
                maxLength={10}
              />
            </Field>
          </div>
        ))}
      </div>
    </Dialog>
  )
}
