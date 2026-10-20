import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2, ExternalLink } from 'lucide-react'
import { PageHeader } from '../../components/PageHeader'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { Dialog, ConfirmDialog } from '../../components/ui/Dialog'
import { Field, Input, Textarea, Select } from '../../components/ui/Field'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'

const emptyTeamForm = { domain_id: '', team_name: '', college: '', order_index: 1 }

export function AdminResultsPage() {
  const { notify } = useToast()
  const [domains, setDomains] = useState(null)
  const [teams, setTeams] = useState(null)
  const [settings, setSettings] = useState(null)
  const [announcement, setAnnouncement] = useState('')
  const [savingSettings, setSavingSettings] = useState(false)
  const [editing, setEditing] = useState(null) // { domainId, team?, form }
  const [deleting, setDeleting] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
    adminApi.listQualifiedTeams().then(({ data }) => setTeams(data))
    adminApi.getResultsSettings().then(({ data }) => {
      setSettings(data)
      setAnnouncement(data.announcement || '')
    })
  }

  useEffect(load, [])

  if (domains === null || teams === null || settings === null) return <PageLoader />

  const byDomainId = {}
  for (const t of teams) {
    if (!byDomainId[t.domain_id]) byDomainId[t.domain_id] = []
    byDomainId[t.domain_id].push(t)
  }
  for (const list of Object.values(byDomainId)) list.sort((a, b) => a.order_index - b.order_index)

  const togglePublish = async () => {
    setSavingSettings(true)
    try {
      const { data } = await adminApi.updateResultsSettings({ is_published: !settings.is_published })
      setSettings(data)
      notify(data.is_published ? 'Results are now live.' : 'Results are now hidden.', 'success')
    } catch (err) {
      notify(getErrorMessage(err, 'Could not update results visibility.'), 'error')
    } finally {
      setSavingSettings(false)
    }
  }

  const saveAnnouncement = async () => {
    setSavingSettings(true)
    try {
      const { data } = await adminApi.updateResultsSettings({ announcement })
      setSettings(data)
      notify('Announcement saved.', 'success')
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save announcement.'), 'error')
    } finally {
      setSavingSettings(false)
    }
  }

  const handleSaveTeam = async (form, teamId) => {
    setSaving(true)
    try {
      const payload = { ...form, order_index: Number(form.order_index) || 1 }
      if (teamId) {
        await adminApi.updateQualifiedTeam(teamId, payload)
      } else {
        await adminApi.createQualifiedTeam(payload)
      }
      notify('Saved.', 'success')
      setEditing(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    try {
      await adminApi.deleteQualifiedTeam(deleting.id)
      notify('Removed.', 'success')
      setDeleting(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err), 'error')
    }
  }

  return (
    <div>
      <PageHeader
        title="Round 1 Results"
        description="Manage the qualified-teams list shown on the public Results page."
        action={
          <a href="/results" target="_blank" rel="noreferrer">
            <Button variant="secondary" size="sm">
              <ExternalLink size={14} /> View Public Page
            </Button>
          </a>
        }
      />

      <Card className="mb-4">
        <CardHeader
          title="Visibility"
          description="Whether the public Results page shows this list yet."
          action={<Badge variant={settings.is_published ? 'success' : 'neutral'}>{settings.is_published ? 'Live' : 'Draft'}</Badge>}
        />
        <CardBody className="flex flex-col gap-4">
          <Field label="Announcement (optional)" hint="Shown at the top of the public Results page.">
            <Textarea
              rows={2}
              value={announcement}
              onChange={(e) => setAnnouncement(e.target.value)}
              placeholder="e.g. Huge congratulations to everyone who made it through Round 1!"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" loading={savingSettings} onClick={saveAnnouncement}>
              Save Announcement
            </Button>
            <Button variant={settings.is_published ? 'danger' : 'accent'} loading={savingSettings} onClick={togglePublish}>
              {settings.is_published ? 'Unpublish Results' : 'Publish Results'}
            </Button>
          </div>
        </CardBody>
      </Card>

      {domains.length === 0 ? (
        <EmptyState title="No domains configured" description="Create domains first." />
      ) : (
        <div className="flex flex-col gap-4">
          {domains.map((domain) => {
            const domainTeams = byDomainId[domain.id] || []
            return (
              <Card key={domain.id}>
                <CardHeader
                  title={domain.name}
                  description={`${domainTeams.length} qualified team${domainTeams.length === 1 ? '' : 's'}`}
                  action={
                    <Button
                      size="sm"
                      onClick={() =>
                        setEditing({
                          domainId: domain.id,
                          team: null,
                          form: { ...emptyTeamForm, domain_id: domain.id, order_index: domainTeams.length + 1 },
                        })
                      }
                    >
                      <Plus size={14} /> Add Team
                    </Button>
                  }
                />
                {domainTeams.length > 0 && (
                  <CardBody className="flex flex-col divide-y divide-ink-100 py-0">
                    {domainTeams.map((t) => (
                      <div key={t.id} className="flex items-center justify-between gap-3 py-3">
                        <div>
                          <p className="text-sm font-medium text-ink-900">{t.team_name}</p>
                          {t.college && <p className="text-xs text-ink-500">{t.college}</p>}
                        </div>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() =>
                              setEditing({
                                domainId: domain.id,
                                team: t,
                                form: {
                                  domain_id: t.domain_id,
                                  team_name: t.team_name,
                                  college: t.college || '',
                                  order_index: t.order_index,
                                },
                              })
                            }
                            className="text-ink-400 hover:text-ink-900"
                            aria-label="Edit"
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            onClick={() => setDeleting(t)}
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

      <TeamDialog state={editing} domains={domains} onClose={() => setEditing(null)} onSave={handleSaveTeam} saving={saving} />

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        danger
        confirmLabel="Remove"
        title="Remove this team from the results?"
        description={`"${deleting?.team_name}" will no longer appear on the public Results page.`}
      />
    </div>
  )
}

function TeamDialog({ state, domains, onClose, onSave, saving }) {
  const [form, setForm] = useState(null)

  useEffect(() => {
    if (state) setForm(state.form)
  }, [state])

  if (!state || !form) return null

  return (
    <Dialog
      open={Boolean(state)}
      onClose={onClose}
      title={state.team ? 'Edit Qualified Team' : 'Add Qualified Team'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={() => onSave(form, state.team?.id)} loading={saving} disabled={!form.team_name.trim()}>
            Save
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Field label="Domain">
          <Select value={form.domain_id} onChange={(e) => setForm({ ...form, domain_id: Number(e.target.value) })}>
            {domains.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Team Name">
          <Input value={form.team_name} onChange={(e) => setForm({ ...form, team_name: e.target.value })} />
        </Field>
        <Field label="College" hint="Optional.">
          <Input value={form.college} onChange={(e) => setForm({ ...form, college: e.target.value })} />
        </Field>
        <Field label="Display Order" hint="Lower numbers show first within the domain.">
          <Input
            type="number"
            min={1}
            value={form.order_index}
            onChange={(e) => setForm({ ...form, order_index: e.target.value })}
          />
        </Field>
      </div>
    </Dialog>
  )
}
