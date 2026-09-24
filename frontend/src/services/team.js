import axios from 'axios'
import { api, tokenStorage } from './api'

export const teamApi = {
  getTeam: () => api.get('/team'),
  getProblemStatement: () => api.get('/team/problem-statement'),
  getHints: () => api.get('/team/hints'),
  getSubmissionState: () => api.get('/team/submission'),
}

export const uploadsApi = {
  presign: (fileType, file) =>
    api.post('/uploads/presign', {
      file_type: fileType,
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      file_size_bytes: file.size,
    }),
  // Uploads go straight to the storage backend's own URL, never through the
  // `/api`-prefixed client: in production this is an absolute S3 URL on a
  // different origin, so it can't use axios's baseURL or carry our JWT.
  uploadToUrl: (uploadUrl, file, onProgress) => {
    const isOwnBackend = uploadUrl.startsWith('/')
    return axios.put(uploadUrl, file, {
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
        ...(isOwnBackend ? { Authorization: `Bearer ${tokenStorage.getAccess()}` } : {}),
      },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100))
      },
    })
  },
  submit: (document, video) => api.post('/submissions', { document, video }),
}

export const publicApi = {
  getDomains: () => api.get('/domains'),
  getTimeline: () => api.get('/public/timeline'),
}
