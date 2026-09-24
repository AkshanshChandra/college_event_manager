import { useEffect, useState } from 'react'
import { PageHeader } from '../../components/PageHeader'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Dialog } from '../../components/ui/Dialog'
import { Field, Input, Textarea } from '../../components/ui/Field'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { PUBLISH_STATUS_META } from '../../utils/status'

export function AdminProblemStatementsPage() {
  const { notify } = useToast()
  const [domains, setDomains] = useState(null)
  const [statements, setStatements] = useState(null)
  const [editingDomain, setEditingDomain] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
    adminApi.listProblemStatements().then(({ data }) => setStatements(data))
  }

  useEffect(load, [])

  if (domains === null || statements === null) return <PageLoader />

  const byDomainId = Object.fromEntries(statements.map((s) => [s.domain_id, s]))

  const handleSave = async (form) => {
    setSaving(true)
    try {
      await adminApi.upsertProblemStatement(form)
      notify('Problem statement saved.', 'success')
      setEditingDomain(null)
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

  return (
    <div>
      <PageHeader title="Problem Statements" description="One problem statement per domain." />

      {domains.length === 0 ? (
        <EmptyState title="No domains configured" description="Create domains first." />
      ) : (
        <div className="flex flex-col gap-4">
          {domains.map((domain) => {
            const ps = byDomainId[domain.id]
            return (
              <Card key={domain.id}>
                <CardHeader
                  title={domain.name}
                  description={ps ? ps.title : 'No problem statement yet.'}
                  action={
                    <div className="flex items-center gap-2">
                      {ps && <StatusBadge meta={PUBLISH_STATUS_META[ps.status]} />}
                      {ps && (
                        <Button variant="secondary" size="sm" onClick={() => togglePublish(ps)}>
                          {ps.status === 'published' ? 'Unpublish' : 'Publish'}
                        </Button>
                      )}
                      <Button
                        size="sm"
                        onClick={() =>
                          setEditingDomain({
                            domain,
                            form: ps || {
                              domain_id: domain.id,
                              title: '',
                              description: '',
                              requirements: '',
                              constraints: '',
                              deliverables: '',
                              supporting_material_url: '',
                            },
                          })
                        }
                      >
                        {ps ? 'Edit' : 'Create'}
                      </Button>
                    </div>
                  }
                />
                {ps && (
                  <CardBody>
                    <p className="line-clamp-2 text-sm text-ink-500">{ps.description}</p>
                  </CardBody>
                )}
              </Card>
            )
          })}
        </div>
      )}

      <ProblemStatementDialog
        state={editingDomain}
        onClose={() => setEditingDomain(null)}
        onSave={handleSave}
        saving={saving}
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
      title={`${state.domain.name} — Problem Statement`}
      size="xl"
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
      <div className="flex max-h-[60vh] flex-col gap-4 overflow-y-auto pr-1">
        <Field label="Title">
          <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <Field label="Description">
          <Textarea rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </Field>
        <Field label="Requirements">
          <Textarea value={form.requirements || ''} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
        </Field>
        <Field label="Constraints">
          <Textarea value={form.constraints || ''} onChange={(e) => setForm({ ...form, constraints: e.target.value })} />
        </Field>
        <Field label="Deliverables">
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
