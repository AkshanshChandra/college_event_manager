import { useCallback, useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { FileDropzone } from '../../components/ui/FileDropzone'
import { ConfirmDialog } from '../../components/ui/Dialog'
import { PageLoader, ErrorState } from '../../components/ui/States'
import { teamApi, uploadsApi } from '../../services/team'
import { getErrorMessage } from '../../services/api'
import { useToast } from '../../hooks/useToast'
import { SUBMISSION_STATUS_META, WINDOW_STATUS_META, formatBytes, formatDateTime } from '../../utils/status'

const emptySlot = { file: null, status: 'idle', progress: 0, error: '', meta: null }

export function SubmissionPage() {
  const { team } = useOutletContext()
  const { notify } = useToast()
  const [state, setState] = useState(null)
  const [error, setError] = useState(false)
  const [doc, setDoc] = useState(emptySlot)
  const [video, setVideo] = useState(emptySlot)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(() => {
    teamApi
      .getSubmissionState()
      .then(({ data }) => setState(data))
      .catch(() => setError(true))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (error) return <ErrorState description="Could not load submission details." />
  if (!state) return <PageLoader />

  const validateFile = (file, kind) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    const allowed = kind === 'document' ? state.allowed_document_extensions : state.allowed_video_extensions
    const maxMb = kind === 'document' ? state.max_document_size_mb : state.max_video_size_mb
    if (!allowed.includes(ext)) {
      return `This file type is not supported. Allowed: ${allowed.join(', ')}.`
    }
    if (file.size > maxMb * 1024 * 1024) {
      return `The selected file exceeds the allowed size of ${maxMb}MB.`
    }
    return null
  }

  const uploadFile = async (file, kind, setSlot) => {
    const validationError = validateFile(file, kind)
    if (validationError) {
      setSlot({ file, status: 'error', progress: 0, error: validationError, meta: null })
      return
    }
    setSlot({ file, status: 'uploading', progress: 0, error: '', meta: null })
    try {
      const { data: presign } = await uploadsApi.presign(kind, file)
      await uploadsApi.uploadToUrl(presign.upload_url, file, (pct) =>
        setSlot((prev) => ({ ...prev, progress: pct }))
      )
      setSlot({
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
      setSlot({ file, status: 'error', progress: 0, error: getErrorMessage(err, 'Upload failed.'), meta: null })
    }
  }

  const handleFinalSubmit = async () => {
    setSubmitting(true)
    try {
      await uploadsApi.submit(doc.meta, video.meta)
      notify('Submission received successfully.', 'success')
      setConfirmOpen(false)
      setDoc(emptySlot)
      setVideo(emptySlot)
      load()
    } catch (err) {
      notify(getErrorMessage(err, 'Could not submit. Please try again.'), 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const windowMeta = WINDOW_STATUS_META[state.window_status]
  const statusMeta = SUBMISSION_STATUS_META[state.participant_status]
  const canUpload =
    state.window_status === 'open' && (!state.active_submission || state.allow_replacement)
  const readyToSubmit = doc.status === 'done' && video.status === 'done'

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-ink-950">Round 1 Submission</h1>
        <div className="flex items-center gap-2">
          <StatusBadge meta={windowMeta} />
          <StatusBadge meta={statusMeta} />
        </div>
      </div>
      <p className="mt-1 text-ink-500">Deadline: {formatDateTime(state.submission_end)}</p>

      {state.window_status === 'not_open' && (
        <Banner icon={AlertTriangle} tone="neutral">
          Submissions open on {formatDateTime(state.submission_start)}.
        </Banner>
      )}
      {state.window_status === 'closed' && (
        <Banner icon={AlertTriangle} tone="danger">
          Round 1 submissions are closed.
        </Banner>
      )}
      {state.window_status === 'open' && state.active_submission && !state.allow_replacement && (
        <Banner icon={AlertTriangle} tone="warning">
          You have already submitted and replacement is not allowed for this round.
        </Banner>
      )}

      {canUpload && (
        <Card className="mt-6">
          <CardHeader
            title="Upload Files"
            description="Both a document and a demo video are required."
          />
          <CardBody className="grid gap-6 sm:grid-cols-2">
            <FileDropzone
              label="PPT / PDF"
              hint={`Allowed: ${state.allowed_document_extensions.join(', ')} · Max ${state.max_document_size_mb}MB`}
              accept={state.allowed_document_extensions.map((e) => `.${e}`).join(',')}
              file={doc.file}
              status={doc.status}
              progress={doc.progress}
              errorMessage={doc.error}
              onSelect={(f) => uploadFile(f, 'document', setDoc)}
              onRetry={() => doc.file && uploadFile(doc.file, 'document', setDoc)}
            />
            <FileDropzone
              label="Demo Video"
              hint={`Allowed: ${state.allowed_video_extensions.join(', ')} · Max ${state.max_video_size_mb}MB`}
              accept={state.allowed_video_extensions.map((e) => `.${e}`).join(',')}
              file={video.file}
              status={video.status}
              progress={video.progress}
              errorMessage={video.error}
              onSelect={(f) => uploadFile(f, 'video', setVideo)}
              onRetry={() => video.file && uploadFile(video.file, 'video', setVideo)}
            />
          </CardBody>
          <div className="flex justify-end border-t border-ink-100 px-5 py-4">
            <Button variant="accent" disabled={!readyToSubmit} onClick={() => setConfirmOpen(true)}>
              Review &amp; Submit
            </Button>
          </div>
        </Card>
      )}

      {state.versions.length > 0 && (
        <Card className="mt-6">
          <CardHeader title="Submission History" description="Most recent version is active." />
          <CardBody className="flex flex-col divide-y divide-ink-100">
            {[...state.versions].reverse().map((v) => (
              <div key={v.id} className="flex items-center justify-between gap-4 py-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-ink-900">Version {v.version}</span>
                    {v.is_active_version && <Badge variant="accent">Active</Badge>}
                  </div>
                  <p className="text-xs text-ink-500">{formatDateTime(v.submitted_at)}</p>
                </div>
                <div className="flex flex-col items-end gap-0.5 text-xs text-ink-500">
                  {v.files.map((f) => (
                    <span key={f.id}>
                      {f.file_type === 'document' ? 'Doc' : 'Video'}: {f.original_filename} (
                      {formatBytes(f.file_size_bytes)})
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleFinalSubmit}
        loading={submitting}
        confirmLabel="Confirm Submission"
        title="Confirm your Round 1 submission"
        description={
          <span>
            <strong>Team:</strong> {team?.name} · <strong>Domain:</strong> {team?.domain?.name}
            <br />
            <strong>Document:</strong> {doc.meta?.original_filename}
            <br />
            <strong>Video:</strong> {video.meta?.original_filename}
            <br />
            <br />
            Once the deadline passes, your submission cannot be changed.
          </span>
        }
      />
    </div>
  )
}

const BANNER_TONES = {
  neutral: 'border-ink-200 bg-ink-50 text-ink-700',
  warning: 'border-warning-100 bg-warning-100 text-warning-600',
  danger: 'border-danger-100 bg-danger-100 text-danger-600',
}

function Banner({ icon: Icon, tone, children }) {
  return (
    <div className={`mt-4 flex items-center gap-2 rounded-md border px-4 py-3 text-sm ${BANNER_TONES[tone]}`}>
      <Icon size={16} className="shrink-0" />
      <span>{children}</span>
    </div>
  )
}
