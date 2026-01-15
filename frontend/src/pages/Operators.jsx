import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { 
  UserCheck, 
  UserX, 
  Play, 
  Pause,
  RefreshCw,
  Bell,
  BellOff,
  Edit
} from 'lucide-react'

export default function Operators() {
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedOperator, setSelectedOperator] = useState(null)
  const { toast } = useToast()

  const fetchOperators = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getOperators()
      setOperators(response.data.operators)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar operadores',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOperators()
  }, [])

  const handlePauseOperator = async (personId, name) => {
    const reason = prompt(`¿Por qué deseas pausar a ${name}?`)
    if (!reason) return

    try {
      await adminApi.pauseOperator(personId, {
        reason,
        paused_by: 'admin',
        performed_by: 'admin'
      })
      toast({
        title: 'Operador Pausado',
        description: `${name} ha sido pausado exitosamente`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al pausar operador',
        variant: 'destructive'
      })
    }
  }

  const handleResumeOperator = async (personId, name) => {
    try {
      await adminApi.resumeOperator(personId)
      toast({
        title: 'Operador Reanudado',
        description: `${name} ha sido reanudado exitosamente`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al reanudar operador',
        variant: 'destructive'
      })
    }
  }

  const handleToggleNotifications = async (personId, name, currentState) => {
    try {
      await adminApi.updateOperator(personId, {
        notifications_enabled: !currentState,
        performed_by: 'admin'
      })
      toast({
        title: 'Notificaciones Actualizadas',
        description: `Notificaciones ${!currentState ? 'activadas' : 'desactivadas'} para ${name}`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar notificaciones',
        variant: 'destructive'
      })
    }
  }

  const handleToggleActive = async (personId, name, currentState) => {
    if (!confirm(`¿Estás seguro de ${currentState ? 'desactivar' : 'activar'} a ${name}?`)) return

    try {
      await adminApi.updateOperator(personId, {
        is_active: !currentState,
        performed_by: 'admin'
      })
      toast({
        title: 'Estado Actualizado',
        description: `${name} ha sido ${!currentState ? 'activado' : 'desactivado'}`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar estado',
        variant: 'destructive'
      })
    }
  }

  const getDayName = (day) => {
    const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    return days[day]
  }

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
          <h1 className="text-3xl font-bold tracking-tight">Gestión de Operadores</h1>
          <p className="text-muted-foreground">
            Administra operadores, pausas y notificaciones
          </p>
        </div>
        <Button onClick={fetchOperators} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Operators Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
        {operators.map((operator) => (
          <Card key={operator.person_id} className={operator.is_paused ? 'border-orange-300' : ''}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="flex items-center gap-2">
                    {operator.name}
                    {operator.is_paused && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                        Pausado
                      </span>
                    )}
                    {!operator.is_active && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Inactivo
                      </span>
                    )}
                  </CardTitle>
                  <CardDescription>
                    ID: {operator.person_id} • WhatsApp: {operator.whatsapp_number || 'No configurado'}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-primary">{operator.ticket_count}</div>
                  <div className="text-xs text-muted-foreground">Asignados</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {operator.schedules?.length || 0}
                  </div>
                  <div className="text-xs text-muted-foreground">Horarios</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">
                    {operator.notifications_enabled ? (
                      <Bell className="h-6 w-6 mx-auto" />
                    ) : (
                      <BellOff className="h-6 w-6 mx-auto" />
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">Notif.</div>
                </div>
              </div>

              {/* Pause Reason */}
              {operator.is_paused && operator.paused_reason && (
                <div className="p-3 bg-orange-50 border border-orange-200 rounded-md">
                  <p className="text-sm text-orange-800">
                    <strong>Razón:</strong> {operator.paused_reason}
                  </p>
                  {operator.paused_at && (
                    <p className="text-xs text-orange-600 mt-1">
                      Pausado: {new Date(operator.paused_at).toLocaleString('es-AR')}
                    </p>
                  )}
                </div>
              )}

              {/* Schedules */}
              {operator.schedules && operator.schedules.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Horarios:</h4>
                  <div className="space-y-1">
                    {operator.schedules.slice(0, 3).map((schedule) => (
                      <div key={schedule.id} className="text-xs text-muted-foreground flex items-center gap-2">
                        <span className="font-medium">{getDayName(schedule.day_of_week)}:</span>
                        <span>{schedule.start_time} - {schedule.end_time}</span>
                      </div>
                    ))}
                    {operator.schedules.length > 3 && (
                      <p className="text-xs text-muted-foreground">
                        +{operator.schedules.length - 3} más...
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-wrap gap-2 pt-2 border-t">
                {operator.is_paused ? (
                  <Button
                    onClick={() => handleResumeOperator(operator.person_id, operator.name)}
                    size="sm"
                    variant="default"
                    className="flex-1"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Reanudar
                  </Button>
                ) : (
                  <Button
                    onClick={() => handlePauseOperator(operator.person_id, operator.name)}
                    size="sm"
                    variant="outline"
                    className="flex-1"
                  >
                    <Pause className="h-4 w-4 mr-2" />
                    Pausar
                  </Button>
                )}

                <Button
                  onClick={() => handleToggleNotifications(operator.person_id, operator.name, operator.notifications_enabled)}
                  size="sm"
                  variant="outline"
                >
                  {operator.notifications_enabled ? (
                    <BellOff className="h-4 w-4" />
                  ) : (
                    <Bell className="h-4 w-4" />
                  )}
                </Button>

                <Button
                  onClick={() => handleToggleActive(operator.person_id, operator.name, operator.is_active)}
                  size="sm"
                  variant={operator.is_active ? "destructive" : "default"}
                >
                  {operator.is_active ? (
                    <UserX className="h-4 w-4" />
                  ) : (
                    <UserCheck className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Resumen</CardTitle>
          <CardDescription>Estado general de operadores</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold">{operators.length}</div>
              <div className="text-sm text-muted-foreground">Total</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {operators.filter(o => o.is_active && !o.is_paused).length}
              </div>
              <div className="text-sm text-muted-foreground">Activos</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">
                {operators.filter(o => o.is_paused).length}
              </div>
              <div className="text-sm text-muted-foreground">Pausados</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-600">
                {operators.filter(o => !o.is_active).length}
              </div>
              <div className="text-sm text-muted-foreground">Inactivos</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
