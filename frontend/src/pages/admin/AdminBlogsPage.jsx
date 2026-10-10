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

const emptyForm = { title: '', content: '' }

export function AdminBlogsPage() {
  const { notify } = useToast()
  const [domains, setDomains] = useState(null)
  const [blogs, setBlogs] = useState(null)
  const [editing, setEditing] = useState(null) // { domain, blog?, form }
  const [deleting, setDeleting] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    adminApi.listDomains().then(({ data }) => setDomains(data))
    adminApi.listBlogs().then(({ data }) => setBlogs(data))
  }

  useEffect(load, [])

  if (domains === null || blogs === null) return <PageLoader />

  const byDomainId = {}
  for (const b of blogs) byDomainId[b.domain_id] = b

  const handleSave = async (form, domainId, blogId) => {
    setSaving(true)
    try {
      if (blogId) {
        await adminApi.updateBlog(blogId, form)
      } else {
        await adminApi.createBlog({ ...form, domain_id: domainId })
      }
      notify('Blog saved.', 'success')
      setEditing(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not save.'), 'error')
    } finally {
      setSaving(false)
    }
  }

  const togglePublish = async (blog) => {
    try {
      await adminApi.setBlogStatus(blog.id, blog.status === 'published' ? 'draft' : 'published')
      notify(blog.status === 'published' ? 'Unpublished.' : 'Published.', 'success')
      load()
    } catch (err) {
      notify(getErrorMessage(err), 'error')
    }
  }

  const handleDelete = async () => {
    try {
      await adminApi.deleteBlog(deleting.id)
      notify('Blog deleted.', 'success')
      setDeleting(null)
      load()
    } catch (err) {
      notify(getErrorMessage(err), 'error')
    }
  }

  return (
    <div>
      <PageHeader
        title="Blogs"
        description="One-time background-reading article per domain (not recurring)."
      />

      {domains.length === 0 ? (
        <EmptyState title="No domains configured" description="Create domains first." />
      ) : (
        <div className="flex flex-col gap-4">
          {domains.map((domain) => {
            const blog = byDomainId[domain.id]
            return (
              <Card key={domain.id}>
                <CardHeader
                  title={domain.name}
                  description={blog ? blog.title : 'No blog article yet'}
                  action={
                    blog ? (
                      <div className="flex items-center gap-3">
                        <StatusBadge meta={PUBLISH_STATUS_META[blog.status]} />
                        <Button variant="secondary" size="sm" onClick={() => togglePublish(blog)}>
                          {blog.status === 'published' ? 'Unpublish' : 'Publish'}
                        </Button>
                        <button
                          onClick={() => setEditing({ domain, blog, form: { title: blog.title, content: blog.content } })}
                          className="text-ink-400 hover:text-ink-900"
                          aria-label="Edit"
                        >
                          <Pencil size={16} />
                        </button>
                        <button
                          onClick={() => setDeleting(blog)}
                          className="text-ink-400 hover:text-danger-600"
                          aria-label="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    ) : (
                      <Button size="sm" onClick={() => setEditing({ domain, blog: null, form: emptyForm })}>
                        <Plus size={14} /> Add Blog
                      </Button>
                    )
                  }
                />
                {blog && (
                  <CardBody>
                    <p className="line-clamp-3 max-w-2xl text-sm text-ink-500">{blog.content}</p>
                  </CardBody>
                )}
              </Card>
            )
          })}
        </div>
      )}

      <BlogDialog state={editing} onClose={() => setEditing(null)} onSave={handleSave} saving={saving} />

      <ConfirmDialog
        open={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        danger
        confirmLabel="Delete"
        title="Delete this blog article?"
        description={`"${deleting?.title}" will be permanently removed.`}
      />
    </div>
  )
}

function BlogDialog({ state, onClose, onSave, saving }) {
  const [form, setForm] = useState(null)

  useEffect(() => {
    if (state) setForm(state.form)
  }, [state])

  if (!state || !form) return null

  return (
    <Dialog
      open={Boolean(state)}
      onClose={onClose}
      title={`${state.domain.name} — ${state.blog ? 'Edit' : 'New'} Blog`}
      size="xl"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={() => onSave(form, state.domain.id, state.blog?.id)} loading={saving}>
            Save
          </Button>
        </>
      }
    >
      <div className="flex max-h-[60vh] flex-col gap-4 overflow-y-auto pr-1">
        <Field label="Title">
          <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        </Field>
        <Field label="Content">
          <Textarea rows={16} value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
        </Field>
      </div>
    </Dialog>
  )
}
