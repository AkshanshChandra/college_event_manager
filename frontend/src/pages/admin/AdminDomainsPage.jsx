import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Card, CardBody } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Dialog } from '../../components/ui/Dialog'
import { Field, Input, Textarea, Select } from '../../components/ui/Field'
import { PageLoader } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'

export function AdminDomainsPage() {
  const { notify } = useToast()
  const [domains, setDomains] = useState(null)
  const [editing, setEditing] = useState(null) // null = closed, {} = create, {...} = edit
  const [saving, setSaving] = useState(false)

  const load = () => adminApi.listDomains().then(({ data }) => setDomains(data))

  useEffect(() => {
    load()
  }, [])

  const handleSave = async (form) => {
    setSaving(true)
    try {
      if (editing.id) {
        await adminApi.updateDomain(editing.id, {
          name: form.name,
          description: form.description,
          status: form.status,
        })
      } else {
        await adminApi.createDomain({ slug: form.slug, name: form.name, description: form.description })
      }
      notify('Domain saved.', 'success')
      setEditing(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save domain.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  if (domains === null) return <PageLoader />

  return (
    <div>
      <PageHeader
        title="Domains"
        description="Configure the competition domains."
        action={
          <Button onClick={() => setEditing({ slug: '', name: '', description: '', status: 'active' })}>
            <Plus size={16} /> New Domain
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {domains.map((d) => (
          <Card key={d.id}>
            <CardBody>
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold text-ink-900">{d.name}</h3>
                <Badge variant={d.status === 'active' ? 'success' : 'neutral'}>{d.status}</Badge>
              </div>
              <p className="mt-1 text-xs text-ink-400">/{d.slug}</p>
              <p className="mt-2 text-sm text-ink-500">{d.description || 'No description yet.'}</p>
              <Button variant="secondary" size="sm" className="mt-3" onClick={() => setEditing(d)}>
                Edit
              </Button>
            </CardBody>
          </Card>
        ))}
      </div>

      <DomainDialog
        domain={editing}
        onClose={() => setEditing(null)}
        onSave={handleSave}
        saving={saving}
      />
    </div>
  )
}

function DomainDialog({ domain, onClose, onSave, saving }) {
  const [form, setForm] = useState({ slug: '', name: '', description: '', status: 'active' })

  useEffect(() => {
    if (domain) setForm({ slug: domain.slug || '', name: domain.name || '', description: domain.description || '', status: domain.status || 'active' })
  }, [domain])

  if (!domain) return null
  const isEdit = Boolean(domain.id)

  return (
    <Dialog
      open={Boolean(domain)}
      onClose={onClose}
      title={isEdit ? 'Edit Domain' : 'New Domain'}
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
        {!isEdit && (
          <Field label="Slug" hint="Lowercase, no spaces. Cannot be changed later.">
            <Input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
          </Field>
        )}
        <Field label="Name">
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </Field>
        <Field label="Description">
          <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        {isEdit && (
          <Field label="Status">
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </Select>
          </Field>
        )}
      </div>
    </Dialog>
  )
}
