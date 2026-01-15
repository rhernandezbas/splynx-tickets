import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, FileText, Filter } from 'lucide-react'

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterAction, setFilterAction] = useState('')
  const [limit, setLimit] = useState(50)
  const { toast } = useToast()

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const params = { limit }
      if (filterAction) {
        params.action = filterAction
      }
      const response = await adminApi.getAuditLogs(params)
      setLogs(response.data.logs)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar logs de auditoría',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [filterAction, limit])

  const getActionBadgeColor = (action) => {
    const colors = {
      'pause_operator': 'bg-orange-100 text-orange-800',
      'resume_operator': 'bg-green-100 text-green-800',
      'update_operator': 'bg-blue-100 text-blue-800',
      'reset_counters': 'bg-purple-100 text-purple-800',
      'update_config': 'bg-yellow-100 text-yellow-800',
      'create_schedule': 'bg-cyan-100 text-cyan-800',
      'update_schedule': 'bg-indigo-100 text-indigo-800',
      'delete_schedule': 'bg-red-100 text-red-800',
    }
    return colors[action] || 'bg-gray-100 text-gray-800'
  }

  const getActionLabel = (action) => {
    const labels = {
      'pause_operator': 'Pausar Operador',
      'resume_operator': 'Reanudar Operador',
      'update_operator': 'Actualizar Operador',
      'reset_counters': 'Reiniciar Contadores',
      'update_config': 'Actualizar Config',
      'create_schedule': 'Crear Horario',
      'update_schedule': 'Actualizar Horario',
      'delete_schedule': 'Eliminar Horario',
      'create_operator': 'Crear Operador',
    }
    return labels[action] || action
  }

  const uniqueActions = [...new Set(logs.map(log => log.action))]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Registro de Auditoría</h1>
          <p className="text-muted-foreground">
            Historial de cambios y acciones en el sistema
          </p>
        </div>
        <Button onClick={fetchLogs} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Filter className="h-5 w-5" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">Acción</label>
              <select
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="w-full px-3 py-2 border rounded-md text-sm"
              >
                <option value="">Todas las acciones</option>
                {uniqueActions.map(action => (
                  <option key={action} value={action}>
                    {getActionLabel(action)}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-32">
              <label className="text-sm font-medium mb-2 block">Límite</label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-md text-sm"
              >
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Registros ({logs.length})
          </CardTitle>
          <CardDescription>
            Últimas {limit} acciones registradas
          </CardDescription>
        </CardHeader>
        <CardContent>
          {logs.length > 0 ? (
            <div className="space-y-3">
              {logs.map((log) => (
                <div key={log.id} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActionBadgeColor(log.action)}`}>
                          {getActionLabel(log.action)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {log.entity_type && `• ${log.entity_type}`}
                          {log.entity_id && ` #${log.entity_id}`}
                        </span>
                      </div>
                      
                      {log.notes && (
                        <p className="text-sm text-gray-700">{log.notes}</p>
                      )}
                      
                      {(log.old_value || log.new_value) && (
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          {log.old_value && (
                            <div className="space-y-1">
                              <div className="font-medium text-gray-600">Valor Anterior:</div>
                              <pre className="bg-gray-100 p-2 rounded overflow-x-auto">
                                {JSON.stringify(log.old_value, null, 2)}
                              </pre>
                            </div>
                          )}
                          {log.new_value && (
                            <div className="space-y-1">
                              <div className="font-medium text-gray-600">Valor Nuevo:</div>
                              <pre className="bg-green-50 p-2 rounded overflow-x-auto">
                                {JSON.stringify(log.new_value, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                      
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>👤 {log.performed_by || 'Sistema'}</span>
                        {log.ip_address && <span>🌐 {log.ip_address}</span>}
                        <span>🕐 {new Date(log.performed_at).toLocaleString('es-AR')}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              No hay registros de auditoría disponibles
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Sobre el Registro de Auditoría</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>• Todos los cambios en el sistema quedan registrados automáticamente</p>
          <p>• Los registros incluyen quién realizó la acción y desde qué IP</p>
          <p>• Se guardan los valores anteriores y nuevos para trazabilidad completa</p>
          <p>• Los registros son permanentes y no se pueden eliminar</p>
        </CardContent>
      </Card>
    </div>
  )
}
