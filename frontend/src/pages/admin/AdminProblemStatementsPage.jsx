import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Dialog, ConfirmDialog } from '../../components/ui/Dialog'
import { Field, Input, Textarea } from '../../components/ui/Field'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { PUBLISH_STATUS_META } from '../../utils/status'

const emptyForm = {
  title: '',
  description: '',
  requirements: '',
  constraints: '',
  deliverables: '',
  supporting_material_url: '',
}

export function AdminProblemStatementsPage() {
  const { notify } = useToast()
  const [domains, setDomains] = useState(null)
  const [statements, setStatements] = useState(null)
  const [editing, setEditing] = useState(null) // { domain, ps?, form }
  const [deleting, setDeleting] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
    adminApi.listProblemStatements().then(({ data }) => setStatements(data))
  }

  useEffect(load, [])

  if (domains === null || statements === null) return <PageLoader />

  const byDomainId = {}
  for (const s of statements) {
    ;(byDomainId[s.domain_id] ||= []).push(s)
  }

  const handleSave = async (form, domainId, psId) => {
    setSaving(true)
    try {
      if (psId) {
        await adminApi.updateProblemStatement(psId, form)
      } else {
        const nextOrder = (byDomainId[domainId]?.length || 0) + 1
        await adminApi.createProblemStatement({ ...form, domain_id: domainId, order_index: nextOrder })
      }
      notify('Problem statement saved.', 'success')
      setEditing(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  const togglePublish = async (ps) => {
    try {
      await adminApi.setProblemStatementStatus(ps.id, ps.status === 'published' ? 'draft' : 'published')
      notify(ps.status === 'published' ? 'Unpublished.' : 'Published.', 'success')
      load()
    } catch (err) {
      notify(getErrorMessage(err), 'error')
    }
  }

  const handleDelete = async () => {
    try {
      await adminApi.deleteProblemStatement(deleting.id)
      notify('Problem statement deleted.', 'success')
      setDeleting(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err), 'error')
    }
  }

  return (
    <div>
      <PageHeader title="Problem Statements" description="Manage the problem statements published for each domain." />

      {domains.length === 0 ? (
        <EmptyState title="No domains configured" description="Create domains first." />
      ) : (
        <div className="flex flex-col gap-6">
          {domains.map((domain) => {
            const items = byDomainId[domain.id] || []
            return (
              <Card key={domain.id}>
                <CardHeader
                  title={domain.name}
                  description={`${items.length} problem statement${items.length === 1 ? '' : 's'}`}
                  action={
                    <Button
                      size="sm"
                      onClick={() => setEditing({ domain, ps: null, form: emptyForm })}
                    >
                      <Plus size={14} /> Add Problem Statement
                    </Button>
                  }
                />
                {items.length > 0 && (
                  <CardBody className="flex flex-col divide-y divide-ink-100">
                    {items.map((ps) => (
                      <div key={ps.id} className="flex items-start justify-between gap-4 py-3 first:pt-0 last:pb-0">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-ink-900">
                              {ps.order_index}. {ps.title}
                            </span>
                            <StatusBadge meta={PUBLISH_STATUS_META[ps.status]} />
                          </div>
                          <p className="mt-1 line-clamp-2 max-w-2xl text-sm text-ink-500">{ps.description}</p>
                        </div>
                        <div className="flex shrink-0 items-center gap-3">
                          <Button variant="secondary" size="sm" onClick={() => togglePublish(ps)}>
                            {ps.status === 'published' ? 'Unpublish' : 'Publish'}
                          </Button>
                          <button
                            onClick={() => setEditing({ domain, ps, form: ps })}
                            className="text-ink-400 hover:text-ink-900"
                            aria-label="Edit"
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            onClick={() => setDeleting(ps)}
                            className="text-ink-400 hover:text-danger-600"
                            aria-label="Delete"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </CardBody>
                )}
              </Card>
            )
          })}
        </div>
      )}

      <ProblemStatementDialog state={editing} onClose={() => setEditing(null)} onSave={handleSave} saving={saving} />

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        danger
        confirmLabel="Delete"
        title="Delete this problem statement?"
        description={`"${deleting?.title}" will be permanently removed.`}
      />
    </div>
  )
}

function ProblemStatementDialog({ state, onClose, onSave, saving }) {
  const [form, setForm] = useState(null)

  useEffect(() => {
    if (state) setForm(state.form)
  }, [state])

  if (!state || !form) return null

  return (
    <Dialog
      open={Boolean(state)}
      onClose={onClose}
      title={`${state.domain.name} — ${state.ps ? 'Edit' : 'New'} Problem Statement`}
      size="xl"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={() => onSave(form, state.domain.id, state.ps?.id)} loading={saving}>
            Save
          </Button>
        </>
      }
    >
      <div className="flex max-h-[60vh] flex-col gap-4 overflow-y-auto pr-1">
        <Field label="Title">
          <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <Field label="Description">
          <Textarea rows={5} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        <Field label="Requirements" hint="Optional">
          <Textarea value={form.requirements || ''} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
        </Field>
        <Field label="Constraints" hint="Optional">
          <Textarea value={form.constraints || ''} onChange={(e) => setForm({ ...form, constraints: e.target.value })} />
        </Field>
        <Field label="Deliverables" hint="Optional">
          <Textarea value={form.deliverables || ''} onChange={(e) => setForm({ ...form, deliverables: e.target.value })} />
        </Field>
        <Field label="Supporting Material URL" hint="Optional link to a reference document.">
          <Input
            value={form.supporting_material_url || ''}
            onChange={(e) => setForm({ ...form, supporting_material_url: e.target.value })}
          />
        </Field>
      </div>
    </Dialog>
  )
}
