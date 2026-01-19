import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, User, Clock, CheckCircle, AlertCircle, TrendingUp, Calendar, Bell, BellOff, FileSearch } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function OperatorView() {
  const [loading, setLoading] = useState(true)
  const [operatorData, setOperatorData] = useState(null)
  const [myTickets, setMyTickets] = useState([])
  const [stats, setStats] = useState(null)
  const [ticketFilter, setTicketFilter] = useState('open') // 'open', 'closed', 'all', 'overdue'
  const [notificationsEnabled, setNotificationsEnabled] = useState(true)
  const [auditModalOpen, setAuditModalOpen] = useState(false)
  const [selectedTicketForAudit, setSelectedTicketForAudit] = useState(null)
  const { toast } = useToast()

  // Obtener el person_id del operador logueado desde sessionStorage
  const currentUser = JSON.parse(sessionStorage.getItem('user') || '{}')
  const personId = currentUser.person_id
  const username = currentUser.username

  const fetchOperatorData = async () => {
    try {
      setLoading(true)
      
      if (!personId) {
        // Si no tiene person_id, mostrar mensaje informativo
        setOperatorData({ name: username || 'Usuario', person_id: null })
        setStats({ assigned: 0, completed: 0, sla_percentage: 100 })
        setMyTickets([])
        return
      }
      
      // Obtener datos del operador
      const operatorsResponse = await adminApi.getOperators()
      const operator = operatorsResponse.data.operators.find(op => op.person_id === personId)
      setOperatorData(operator)
      
      // Sincronizar estado de notificaciones desde BD
      // Notificaciones activas si: notifications_enabled=true Y está en horario de trabajo
      if (operator) {
        const manuallyEnabled = operator.notifications_enabled !== false
        const inWorkingHours = operator.is_active && !operator.is_paused
        setNotificationsEnabled(manuallyEnabled && inWorkingHours)
      }

      // Obtener métricas del operador del mes actual
      const now = new Date()
      const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
      
      const metricsResponse = await adminApi.getMetrics()
      const operatorMetrics = metricsResponse.data.metrics.operator_distribution?.find(
        op => op.person_id === personId
      )
      setStats(operatorMetrics)

      // Obtener tickets reales asignados al operador con filtro de estado
      try {
        let ticketsResponse
        if (ticketFilter === 'overdue') {
          // Para vencidos, obtener todos y filtrar por exceeded_threshold
          ticketsResponse = await adminApi.getIncidents({ 
            assigned_to: personId,
            ticket_status: 'all'
          })
        } else {
          ticketsResponse = await adminApi.getIncidents({ 
            assigned_to: personId,
            ticket_status: ticketFilter
          })
        }
        const tickets = ticketsResponse.data.incidents || []
        
        // Función para parsear fecha DD-MM-YYYY
        const parseDate = (dateStr) => {
          if (!dateStr) return null
          const parts = dateStr.split(' ')
          const dateParts = parts[0].split('-')
          const year = dateParts[2]
          const month = dateParts[1]
          const day = dateParts[0]
          return new Date(`${year}-${month}-${day}`)
        }
        
        // Filtrar según el tipo
        let filteredTickets = tickets
        if (ticketFilter === 'overdue') {
          filteredTickets = tickets.filter(t => t.exceeded_threshold)
        }
        
        // Transformar al formato esperado
        const formattedTickets = filteredTickets.map(ticket => ({
          id: ticket.id,
          ticket_id: ticket.ticket_id,
          cliente: ticket.customer_name,
          asunto: ticket.subject,
          estado: ticket.status_name,
          prioridad: ticket.priority_name,
          created_at: ticket.created_at,
          assigned_at: ticket.created_at,
          is_closed: ticket.is_closed,
          closed_at: ticket.closed_at,
          exceeded_threshold: ticket.exceeded_threshold,
          audit_requested: ticket.audit_requested,
          audit_status: ticket.audit_status,
          audit_notified: ticket.audit_notified,
          audit_requested_at: ticket.audit_requested_at,
          audit_requested_by: ticket.audit_requested_by,
          recreado: ticket.recreado || 0
        }))
        
        setMyTickets(formattedTickets)
        
        // Calcular métricas localmente solo del mes actual
        const allTicketsResponse = await adminApi.getIncidents({ 
          assigned_to: personId,
          ticket_status: 'all'
        })
        const allTickets = allTicketsResponse.data.incidents || []
        
        // Filtrar tickets del mes actual
        const monthlyTickets = allTickets.filter(t => {
          const ticketDate = parseDate(t.created_at)
          return ticketDate && 
                 ticketDate >= firstDayOfMonth && 
                 ticketDate <= lastDayOfMonth
        })
        
        const openCount = monthlyTickets.filter(t => !t.is_closed).length
        const closedCount = monthlyTickets.filter(t => t.is_closed).length
        const totalCount = monthlyTickets.length
        
        // Calcular SLA mensual
        const exceededCount = monthlyTickets.filter(t => t.exceeded_threshold).length
        const withinSLA = totalCount - exceededCount
        const monthlySLA = totalCount > 0 ? ((withinSLA / totalCount) * 100) : 100
        
        setStats({
          assigned: openCount,
          completed: closedCount,
          total: totalCount,
          sla_percentage: monthlySLA
        })
      } catch (error) {
        console.error('Error al cargar tickets:', error)
        setMyTickets([])
      }

    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar datos',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleRequestAudit = async () => {
    if (!selectedTicketForAudit) return
    
    try {
      await adminApi.requestTicketAudit(selectedTicketForAudit.ticket_id, {
        person_id: personId
      })
      
      toast({
        title: '✅ Auditoría solicitada',
        description: `El ticket #${selectedTicketForAudit.ticket_id} ha sido marcado para auditoría. El admin será notificado.`
      })
      
      setAuditModalOpen(false)
      setSelectedTicketForAudit(null)
      fetchOperatorData()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'No se pudo solicitar la auditoría',
        variant: 'destructive'
      })
    }
  }

  useEffect(() => {
    fetchOperatorData()
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchOperatorData, 30000)
    return () => clearInterval(interval)
  }, [ticketFilter])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!operatorData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-lg font-medium">No se encontró información del operador</p>
        </div>
      </div>
    )
  }

  const openTickets = myTickets.filter(t => !t.is_closed)
  const closedTickets = myTickets.filter(t => t.is_closed)

  const overdueTickets = myTickets.filter(t => t.exceeded_threshold && !t.is_closed)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mi Panel de Operador</h1>
          <p className="text-muted-foreground">
            Bienvenido, {operatorData.name}
          </p>
        </div>
        <Button onClick={fetchOperatorData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Mensaje informativo si no tiene person_id */}
      {!personId && (
        <Card className="border-blue-300 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-900">
              <AlertCircle className="h-5 w-5" />
              Configuración Pendiente
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-blue-800">
              Tu cuenta de operador aún no está vinculada a un operador del sistema. 
              Por favor, contacta al administrador para que te asigne un <strong>person_id</strong> y 
              puedas ver tus tickets asignados y métricas de rendimiento.
            </p>
            <p className="text-blue-800 mt-2">
              Mientras tanto, puedes acceder a la página de <strong>Métricas</strong> para ver 
              información general del sistema.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Estado del Operador */}
      <Card className={
        operatorData.is_paused ? 'border-orange-300 bg-orange-50' :
        operatorData.is_active ? 'border-green-300 bg-green-50' :
        'border-gray-300 bg-gray-50'
      }>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Estado Actual
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Estado</p>
              <p className="text-lg font-semibold">
                {operatorData.is_paused ? (
                  <span className="text-orange-600">⏸️ Pausado</span>
                ) : operatorData.is_active ? (
                  <span className="text-green-600">✅ Activo</span>
                ) : (
                  <span className="text-gray-600">⭕ Inactivo</span>
                )}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Notificaciones WhatsApp</p>
              <p className="text-lg font-semibold">
                {notificationsEnabled ? (
                  <span className="text-green-600">✅ Habilitadas</span>
                ) : (
                  <span className="text-red-600">🔕 Deshabilitadas</span>
                )}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Tickets Asignados Hoy</p>
              <p className="text-lg font-semibold text-blue-600">
                {stats?.assigned || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      
      {/* Tickets Vencidos - Alerta */}
      {overdueTickets.length > 0 && (
        <Card className="border-red-300 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-900">
              <AlertCircle className="h-5 w-5" />
              ⚠️ Tickets Vencidos Asignados a Ti
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-800 mb-3">
              Tienes <strong>{overdueTickets.length}</strong> ticket(s) que han excedido el tiempo de respuesta esperado.
            </p>
            <div className="space-y-2">
              {overdueTickets.slice(0, 5).map(ticket => (
                <div key={ticket.id} className="bg-white p-3 rounded border border-red-200">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-red-700">#{ticket.ticket_id}</span>
                    <span className="text-xs text-red-600">{ticket.prioridad}</span>
                  </div>
                  <p className="text-sm text-gray-700 truncate">{ticket.asunto}</p>
                  <p className="text-xs text-gray-500 mt-1">{ticket.cliente}</p>
                </div>
              ))}
              {overdueTickets.length > 5 && (
                <p className="text-xs text-red-600 text-center">+ {overdueTickets.length - 5} más</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPIs del Operador */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tickets Activos</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.assigned || 0}</div>
            <p className="text-xs text-muted-foreground">
              Pendientes de resolver
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tickets Cerrados</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.completed || 0}</div>
            <p className="text-xs text-muted-foreground">
              Resueltos exitosamente
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Manejados</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              Tickets totales
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SLA Mensual</CardTitle>
            <TrendingUp className={`h-4 w-4 ${(stats?.sla_percentage || 100) >= 90 ? 'text-green-600' : (stats?.sla_percentage || 100) >= 70 ? 'text-yellow-600' : 'text-red-600'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${(stats?.sla_percentage || 100) >= 90 ? 'text-green-600' : (stats?.sla_percentage || 100) >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
              {(stats?.sla_percentage || 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Cumplimiento de SLA (mes actual)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Horarios de Trabajo */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Mis Horarios de Trabajo
          </CardTitle>
          <CardDescription>Horarios configurados para esta semana</CardDescription>
        </CardHeader>
        <CardContent>
          {operatorData.schedules && operatorData.schedules.length > 0 ? (
            <div className="space-y-2">
              {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'].map((day, index) => {
                const daySchedules = operatorData.schedules.filter(s => 
                  s.day_of_week === index && s.schedule_type === 'assignment'
                )
                return (
                  <div key={day} className="flex items-center justify-between py-2 border-b last:border-0">
                    <span className="font-medium text-sm w-32">{day}</span>
                    <div className="flex-1">
                      {daySchedules.length > 0 ? (
                        <div className="flex gap-2 flex-wrap">
                          {daySchedules.map(schedule => (
                            <span
                              key={schedule.id}
                              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                schedule.is_active ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {schedule.start_time} - {schedule.end_time}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">Sin horario</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-4">
              No hay horarios configurados
            </p>
          )}
        </CardContent>
      </Card>

      {/* Mis Tickets */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Mis Tickets Asignados</CardTitle>
              <CardDescription>Tickets actualmente bajo tu responsabilidad</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setTicketFilter('open')}
                variant={ticketFilter === 'open' ? 'default' : 'outline'}
                size="sm"
              >
                Abiertos
              </Button>
              <Button
                onClick={() => setTicketFilter('closed')}
                variant={ticketFilter === 'closed' ? 'default' : 'outline'}
                size="sm"
              >
                Cerrados
              </Button>
              <Button
                onClick={() => setTicketFilter('all')}
                variant={ticketFilter === 'all' ? 'default' : 'outline'}
                size="sm"
              >
                Todos
              </Button>
              <Button
                onClick={() => setTicketFilter('overdue')}
                variant={ticketFilter === 'overdue' ? 'default' : 'outline'}
                size="sm"
              >
                Vencidos
              </Button>
                          </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2 font-medium">ID</th>
                  <th className="text-left p-2 font-medium">Cliente</th>
                  <th className="text-left p-2 font-medium">Asunto</th>
                  <th className="text-left p-2 font-medium">Estado</th>
                  <th className="text-left p-2 font-medium">Prioridad</th>
                  <th className="text-left p-2 font-medium">Asignado</th>
                  <th className="text-left p-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {myTickets.length > 0 ? (
                  myTickets.map((ticket) => (
                    <tr key={ticket.id} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-mono text-xs">{ticket.ticket_id}</td>
                      <td className="p-2">{ticket.cliente}</td>
                      <td className="p-2 max-w-xs truncate">
                        <div className="flex flex-col gap-1">
                          <span className={ticket.recreado > 0 ? "text-red-600 font-semibold" : ""}>
                            {ticket.asunto}
                          </span>
                          {ticket.recreado > 0 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              🔄 Recreado x{ticket.recreado}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="flex flex-col gap-1">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            ticket.estado === 'Cerrado' ? 'bg-green-100 text-green-800' :
                            ticket.estado === 'Abierto' ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {ticket.estado}
                          </span>
                          {ticket.exceeded_threshold && !ticket.is_closed && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              ⚠️ Vencido
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.prioridad === 'Alta' ? 'bg-red-100 text-red-800' :
                          ticket.prioridad === 'Media' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {ticket.prioridad}
                        </span>
                      </td>
                      <td className="p-2 text-xs text-gray-600">
                        {new Date(ticket.assigned_at).toLocaleString()}
                      </td>
                      <td className="p-2">
                        <div className="flex flex-col gap-1">
                          {/* Mostrar estado de auditoría si existe */}
                          {ticket.audit_status === 'approved' && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              ✅ Revisado
                            </span>
                          )}
                          {ticket.audit_status === 'rejected' && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 font-bold">
                              ❌ Rechazado en Auditoría
                            </span>
                          )}
                          {ticket.audit_status === 'pending' && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                              ⏳ En revisión
                            </span>
                          )}
                          {/* Botón Auditar solo si no ha solicitado auditoría y no tiene estado de auditoría */}
                          {ticket.exceeded_threshold && !ticket.audit_requested && !ticket.audit_status && (
                            <Button
                              onClick={() => {
                                setSelectedTicketForAudit(ticket)
                                setAuditModalOpen(true)
                              }}
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                            >
                              <FileSearch className="h-3 w-3 mr-1" />
                              Auditar
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="p-8 text-center text-muted-foreground">
                      No tienes tickets asignados actualmente
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Información */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Información Importante</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>• Esta vista se actualiza automáticamente cada 30 segundos</p>
          <p>• Los tickets se asignan automáticamente según tu disponibilidad y horarios</p>
          <p>• Si estás pausado, no recibirás nuevas asignaciones</p>
          <p>• Las notificaciones de WhatsApp te alertarán sobre tickets vencidos y fin de turno</p>
          <p>• Para cambios en tu configuración, contacta al administrador</p>
        </CardContent>
      </Card>

      {/* Modal de Auditoría */}
      {auditModalOpen && selectedTicketForAudit && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <FileSearch className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Solicitar Auditoría</h3>
                  <p className="text-sm text-gray-500">Ticket #{selectedTicketForAudit.ticket_id}</p>
                </div>
              </div>
              
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700 mb-2">Detalles del ticket:</p>
                <p className="text-sm text-gray-600 mb-1"><strong>Cliente:</strong> {selectedTicketForAudit.cliente}</p>
                <p className="text-sm text-gray-600 mb-1"><strong>Asunto:</strong> {selectedTicketForAudit.asunto}</p>
                <p className="text-sm text-gray-600"><strong>Prioridad:</strong> {selectedTicketForAudit.prioridad}</p>
              </div>

              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  ℹ️ Al confirmar, este ticket será marcado para auditoría y el administrador será notificado para revisión manual.
                </p>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setAuditModalOpen(false)
                    setSelectedTicketForAudit(null)
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleRequestAudit}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  Confirmar Auditoría
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
