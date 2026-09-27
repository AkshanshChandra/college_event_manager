import { api } from './api'

export const registrationApi = {
  checkTeamName: (teamName) => api.get('/registrations/check-team-name', { params: { team_name: teamName } }),
  submit: (payload) => api.post('/registrations', payload),

  presignPaymentScreenshot: (registrationId, email, file) =>
    api.post(`/registrations/${registrationId}/payment-screenshot/presign`, {
      email,
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      file_size_bytes: file.size,
    }),
  confirmPaymentScreenshot: (registrationId, email, meta) =>
    api.post(`/registrations/${registrationId}/payment-screenshot/confirm`, { email, ...meta }),
}
