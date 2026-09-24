import { useEffect, useState } from 'react'
import { PageHeader } from '../../components/PageHeader'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Field, Input } from '../../components/ui/Field'
import { PageLoader } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'

function toLocalInputValue(iso) {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function AdminSettingsPage() {
  const { notify } = useToast()
  const [settings, setSettings] = useState(null)
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    adminApi.getSettings().then(({ data }) => {
      setSettings(data)
      setForm({
        ...data,
        submission_start: toLocalInputValue(data.submission_start),
        submission_end: toLocalInputValue(data.submission_end),
      })
    })
  }, [])

  if (!settings || !form) return <PageLoader />

  const handleSave = async () => {
    setSaving(true)
    try {
      const { data } = await adminApi.updateSettings({
        round_label: form.round_label,
        submission_start: new Date(form.submission_start).toISOString(),
        submission_end: new Date(form.submission_end).toISOString(),
        allow_replacement: form.allow_replacement,
        max_document_size_mb: Number(form.max_document_size_mb),
        max_video_size_mb: Number(form.max_video_size_mb),
        allowed_document_extensions: form.allowed_document_extensions,
        allowed_video_extensions: form.allowed_video_extensions,
      })
      setSettings(data)
      notify('Settings saved.', 'success')
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save settings.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Competition Settings" description="Configure Round 1 submission rules." />

      <Card>
        <CardHeader title={form.round_label} />
        <CardBody className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Submission Start">
              <Input
                type="datetime-local"
                value={form.submission_start}
                onChange={(e) => setForm({ ...form, submission_start: e.target.value })}
              />
            </Field>
            <Field label="Submission End">
              <Input
                type="datetime-local"
                value={form.submission_end}
                onChange={(e) => setForm({ ...form, submission_end: e.target.value })}
              />
            </Field>
          </div>

          <Field label="Allow Replacement" hint="Whether teams can replace a submission before the deadline.">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.allow_replacement}
                onChange={(e) => setForm({ ...form, allow_replacement: e.target.checked })}
                className="h-4 w-4 rounded border-ink-300 text-accent-600 focus:ring-accent-500"
              />
              <span className="text-sm text-ink-700">Teams may re-upload before the deadline</span>
            </div>
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Max Document Size (MB)">
              <Input
                type="number"
                min={1}
                value={form.max_document_size_mb}
                onChange={(e) => setForm({ ...form, max_document_size_mb: e.target.value })}
              />
            </Field>
            <Field label="Max Video Size (MB)">
              <Input
                type="number"
                min={1}
                value={form.max_video_size_mb}
                onChange={(e) => setForm({ ...form, max_video_size_mb: e.target.value })}
              />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Allowed Document Extensions" hint="Comma-separated, no dots.">
              <Input
                value={form.allowed_document_extensions}
                onChange={(e) => setForm({ ...form, allowed_document_extensions: e.target.value })}
              />
            </Field>
            <Field label="Allowed Video Extensions" hint="Comma-separated, no dots.">
              <Input
                value={form.allowed_video_extensions}
                onChange={(e) => setForm({ ...form, allowed_video_extensions: e.target.value })}
              />
            </Field>
          </div>
        </CardBody>
        <div className="flex justify-end border-t border-ink-100 px-5 py-4">
          <Button onClick={handleSave} loading={saving}>
            Save Settings
          </Button>
        </div>
      </Card>
    </div>
  )
}
