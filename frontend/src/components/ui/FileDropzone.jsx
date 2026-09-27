import { useRef } from 'react'
import { UploadCloud, CheckCircle2, XCircle, Loader2, RotateCcw } from 'lucide-react'
import { formatBytes } from '../../utils/status'

export function FileDropzone({
  label,
  hint,
  accept,
  file,
  status, // 'idle' | 'uploading' | 'done' | 'error'
  progress = 0,
  errorMessage,
  onSelect,
  onRetry,
  disabled,
}) {
  const inputRef = useRef(null)

  const handleFiles = (files) => {
    if (files?.[0]) onSelect(files[0])
  }

  return (
    <div>
      <p className="text-sm font-medium text-ink-800">{label}</p>
      {hint && <p className="mt-0.5 text-xs text-ink-500">{hint}</p>}

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          if (!disabled) handleFiles(e.dataTransfer.files)
        }}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`mt-2 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors ${
          disabled ? 'cursor-not-allowed border-ink-100 bg-ink-50' : 'border-ink-200 hover:border-accent-400 hover:bg-accent-600/10'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          disabled={disabled}
          onChange={(e) => handleFiles(e.target.files)}
        />

        {status === 'uploading' ? (
          <>
            <Loader2 size={22} className="animate-spin text-accent-600" />
            <p className="text-sm text-ink-600">Uploading… {progress}%</p>
            <div className="h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-ink-100">
              <div className="h-full bg-accent-600 transition-all" style={{ width: `${progress}%` }} />
            </div>
          </>
        ) : status === 'done' && file ? (
          <>
            <CheckCircle2 size={22} className="text-success-600" />
            <p className="text-sm font-medium text-ink-900">{file.name}</p>
            <p className="text-xs text-ink-500">{formatBytes(file.size)} · Uploaded</p>
          </>
        ) : status === 'error' ? (
          <>
            <XCircle size={22} className="text-danger-600" />
            <p className="text-sm text-danger-600">{errorMessage || 'Upload failed.'}</p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                onRetry?.()
              }}
              className="mt-1 flex items-center gap-1 text-xs font-medium text-accent-700 hover:underline"
            >
              <RotateCcw size={12} /> Try again
            </button>
          </>
        ) : (
          <>
            <UploadCloud size={22} className="text-ink-400" />
            <p className="text-sm text-ink-600">
              <span className="font-medium text-accent-700">Click to upload</span> or drag and drop
            </p>
          </>
        )}
      </div>
    </div>
  )
}
