import { useEffect, useState } from 'react'
import { PageHeader } from '../../components/PageHeader'
import { Table, Td } from '../../components/ui/Table'
import { PageLoader, EmptyState } from '../../components/ui/States'
import { adminApi } from '../../services/admin'
import { formatDateTime } from '../../utils/status'

export function AdminAuditLogsPage() {
  const [logs, setLogs] = useState(null)

  useEffect(() => {
    adminApi.listAuditLogs().then(({ data }) => setLogs(data))
  }, [])

  if (logs === null) return <PageLoader />

  return (
    <div>
      <PageHeader title="Audit Logs" description="Recent organizer actions." />

      {logs.length === 0 ? (
        <EmptyState title="No activity yet" description="Admin actions will be recorded here." />
      ) : (
        <Table columns={['Action', 'Entity', 'Entity ID', 'When']}>
          {logs.map((log) => (
            <tr key={log.id}>
              <Td className="font-medium text-ink-900">{log.action}</Td>
              <Td className="capitalize">{log.entity_type.replace('_', ' ')}</Td>
              <Td>{log.entity_id ?? '—'}</Td>
              <Td>{formatDateTime(log.created_at)}</Td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  )
}
