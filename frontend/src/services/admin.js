import { api } from './api'

export const adminApi = {
  getDashboard: () => api.get('/admin/dashboard'),
  syncRegistrations: () => api.post('/admin/sync-registrations'),
  pushRegistrationsToSheet: () => api.post('/admin/registrations/sync-to-sheet'),

  listRegistrations: (params) => api.get('/admin/registrations', { params }),
  // A plain <a href> can't carry the Authorization header this endpoint
  // requires (browser navigation sends no auth headers at all), so the
  // download has to go through axios as a blob and be saved client-side.
  exportRegistrationsCsv: () => api.get('/admin/registrations/export', { responseType: 'blob' }),
  updatePaymentStatus: (id, paymentStatus) =>
    api.put(`/admin/registrations/${id}/payment-status`, { payment_status: paymentStatus }),

  listTeams: (params) => api.get('/admin/teams', { params }),
  getTeamDetail: (teamId) => api.get(`/admin/teams/${teamId}`),

  listDomains: () => api.get('/admin/domains'),
  createDomain: (payload) => api.post('/admin/domains', payload),
  updateDomain: (id, payload) => api.put(`/admin/domains/${id}`, payload),

  listProblemStatements: () => api.get('/admin/problem-statements'),
  createProblemStatement: (payload) => api.post('/admin/problem-statements', payload),
  updateProblemStatement: (id, payload) => api.put(`/admin/problem-statements/${id}`, payload),
  deleteProblemStatement: (id) => api.delete(`/admin/problem-statements/${id}`),
  setProblemStatementStatus: (id, status) =>
    api.put(`/admin/problem-statements/${id}/publish`, null, { params: { status } }),

  listHints: () => api.get('/admin/hints'),
  createHint: (payload) => api.post('/admin/hints', payload),
  updateHint: (id, payload) => api.put(`/admin/hints/${id}`, payload),
  deleteHint: (id) => api.delete(`/admin/hints/${id}`),

  listSubmissions: (params) => api.get('/admin/submissions', { params }),
  getSubmissionDetail: (id) => api.get(`/admin/submissions/${id}`),

  getSettings: () => api.get('/admin/settings'),
  updateSettings: (payload) => api.put('/admin/settings', payload),

  listAuditLogs: (params) => api.get('/admin/audit-logs', { params }),
}
