import { api } from './api'

export const registrationApi = {
  checkTeamName: (teamName) => api.get('/registrations/check-team-name', { params: { team_name: teamName } }),
  // The registration is only ever created once, atomically, alongside its
  // payment outcome (an uploaded screenshot for online, or a cash choice) —
  // there's no earlier "create the row" call, so nothing is recorded for a
  // form that gets abandoned before payment.
  submit: (payload) => api.post('/registrations', payload),

  presignPaymentScreenshot: (file) =>
    api.post('/registrations/payment-screenshot/presign', {
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      file_size_bytes: file.size,
    }),
}
