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
  updateRegistration: (id, payload) => api.put(`/admin/registrations/${id}`, payload),
  resendRegistrationEmail: (id) => api.post(`/admin/registrations/${id}/resend-email`),
  mergeRegistrations: (primaryRegistrationId, secondaryRegistrationId) =>
    api.post('/admin/registrations/merge', {
      primary_registration_id: primaryRegistrationId,
      secondary_registration_id: secondaryRegistrationId,
    }),

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

  listBlogs: () => api.get('/admin/blogs'),
  createBlog: (payload) => api.post('/admin/blogs', payload),
  updateBlog: (id, payload) => api.put(`/admin/blogs/${id}`, payload),
  deleteBlog: (id) => api.delete(`/admin/blogs/${id}`),
  setBlogStatus: (id, status) => api.put(`/admin/blogs/${id}/publish`, null, { params: { status } }),

  listSubmissions: (params) => api.get('/admin/submissions', { params }),
  getSubmissionDetail: (id) => api.get(`/admin/submissions/${id}`),
  exportSubmissionsZip: () => api.get('/admin/submissions/export-zip'),

  getSettings: () => api.get('/admin/settings'),
  updateSettings: (payload) => api.put('/admin/settings', payload),

  getRegistrationSettings: () => api.get('/admin/registration-settings'),
  updateRegistrationSettings: (isOpen) => api.put('/admin/registration-settings', { is_open: isOpen }),

  listAuditLogs: (params) => api.get('/admin/audit-logs', { params }),
}
