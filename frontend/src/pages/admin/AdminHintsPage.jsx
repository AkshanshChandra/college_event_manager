import { useEffect, useState } from 'react'
import { Plus, Trash2, Pencil } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Table, Td } from '../../components/ui/Table'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Dialog, ConfirmDialog } from '../../components/ui/Dialog'
import { Field, Input, Textarea, Select } from '../../components/ui/Field'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { PUBLISH_STATUS_META, formatDateTime } from '../../utils/status'

function toLocalInputValue(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const emptyForm = {
  week_number: 1,
  title: '',
  content: '',
  scope: 'global',
  domain_id: null,
  publish_at: toLocalInputValue(new Date().toISOString()),
  status: 'draft',
}

export function AdminHintsPage() {
  const { notify } = useToast()
  const [hints, setHints] = useState(null)
  const [domains, setDomains] = useState([])
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => adminApi.listHints().then(({ data }) => setHints(data))

  useEffect(() => {
    load()
    adminApi.listDomains().then(({ data }) => setDomains(data))
  }, [])

  const handleSave = async (form) => {
    setSaving(true)
    const payload = { ...form, publish_at: new Date(form.publish_at).toISOString() }
    try {
      if (editing.id) {
        await adminApi.updateHint(editing.id, payload)
      } else {
        await adminApi.createHint(payload)
      }
      notify('Hint saved.', 'success')
      setEditing(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save hint.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    try {
      await adminApi.deleteHint(deleting.id)
      notify('Hint deleted.', 'success')
      setDeleting(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err), 'error')
    }
  }

  if (hints === null) return <PageLoader />

  return (
    <div>
      <PageHeader
        title="Weekly Hints"
        description="Publish guidance for participants."
        action={
          <Button onClick={() => setEditing({ form: emptyForm })}>
            <Plus size={16} /> New Hint
          </Button>
        }
      />

      {hints.length === 0 ? (
        <EmptyState title="No hints yet" description="Create your first weekly hint." />
      ) : (
        <Table columns={['Week', 'Title', 'Scope', 'Publish At', 'Status', '']}>
          {hints.map((h) => (
            <tr key={h.id}>
              <Td>{h.week_number}</Td>
              <Td className="font-medium text-ink-900">{h.title}</Td>
              <Td>
                <Badge variant="neutral">
                  {h.scope === 'global' ? 'Global' : domains.find((d) => d.id === h.domain_id)?.name || 'Domain'}
                </Badge>
              </Td>
              <Td>{formatDateTime(h.publish_at)}</Td>
              <Td>
                <StatusBadge meta={PUBLISH_STATUS_META[h.status]} />
              </Td>
              <Td>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() =>
                      setEditing({
                        id: h.id,
                        form: { ...h, publish_at: toLocalInputValue(h.publish_at) },
                      })
                    }
                    className="text-ink-500 hover:text-ink-900"
                    aria-label="Edit"
                  >
                    <Pencil size={16} />
                  </button>
                  <button
                    onClick={() => setDeleting(h)}
                    className="text-ink-500 hover:text-danger-600"
                    aria-label="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </Td>
            </tr>
          ))}
        </Table>
      )}

      <HintDialog
        state={editing}
        domains={domains}
        onClose={() => setEditing(null)}
        onSave={handleSave}
        saving={saving}
      />

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        danger
        confirmLabel="Delete Hint"
        title="Delete this hint?"
        description={`"${deleting?.title}" will be permanently removed.`}
      />
    </div>
  )
}

function HintDialog({ state, domains, onClose, onSave, saving }) {
  const [form, setForm] = useState(null)

  useEffect(() => {
    if (state) setForm(state.form)
  }, [state])

  if (!state || !form) return null

  return (
    <Dialog
      open={Boolean(state)}
      onClose={onClose}
      title={state.id ? 'Edit Hint' : 'New Hint'}
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={() => onSave(form)} loading={saving}>
            Save
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Week Number">
            <Input
              type="number"
              min={1}
              value={form.week_number}
              onChange={(e) => setForm({ ...form, week_number: Number(e.target.value) })}
            />
          </Field>
          <Field label="Status">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </Select>
          </Field>
        </div>
        <Field label="Title">
          <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <Field label="Content">
          <Textarea rows={5} value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Scope">
            <Select
              value={form.scope}
              onChange={(e) => setForm({ ...form, scope: e.target.value, domain_id: e.target.value === 'global' ? null : form.domain_id })}
            >
              <option value="global">Global (all teams)</option>
              <option value="domain">Domain-specific</option>
            </Select>
          </Field>
          {form.scope === 'domain' && (
            <Field label="Domain">
              <Select
                value={form.domain_id || ''}
                onChange={(e) => setForm({ ...form, domain_id: Number(e.target.value) })}
              >
                <option value="" disabled>
                  Select domain
                </option>
                {domains.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </Select>
            </Field>
          )}
        </div>
        <Field label="Publish At">
          <Input
            type="datetime-local"
            value={form.publish_at}
            onChange={(e) => setForm({ ...form, publish_at: e.target.value })}
          />
        </Field>
      </div>
    </Dialog>
  )
}
