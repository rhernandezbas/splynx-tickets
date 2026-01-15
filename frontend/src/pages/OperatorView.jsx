import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, User, Clock, CheckCircle, AlertCircle, TrendingUp, Calendar } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function OperatorView() {
  const [loading, setLoading] = useState(true)
  const [operatorData, setOperatorData] = useState(null)
  const [myTickets, setMyTickets] = useState([])
  const [stats, setStats] = useState(null)
  const { toast } = useToast()

  // Obtener el person_id del operador logueado desde sessionStorage
  const currentUser = JSON.parse(sessionStorage.getItem('user') || '{}')
  const personId = currentUser.person_id

  const fetchOperatorData = async () => {
    try {
      setLoading(true)
      
      // Obtener datos del operador
      const operatorsResponse = await adminApi.getOperators()
      const operator = operatorsResponse.data.operators.find(op => op.person_id === personId)
      setOperatorData(operator)

      // Obtener métricas del operador
      const metricsResponse = await adminApi.getMetrics()
      const operatorMetrics = metricsResponse.data.metrics.operator_distribution?.find(
        op => op.person_id === personId
      )
      setStats(operatorMetrics)

      // Aquí deberías obtener los tickets asignados al operador
      // Por ahora usamos datos de ejemplo
      const mockTickets = [
        {
          id: 1,
          ticket_id: 'T-001',
          cliente: 'Cliente A',
          asunto: 'Problema de conexión',
          estado: 'En Progreso',
          prioridad: 'Alta',
          created_at: '2026-01-14T10:00:00',
          assigned_at: '2026-01-14T10:05:00'
        },
        {
          id: 2,
          ticket_id: 'T-002',
          cliente: 'Cliente B',
          asunto: 'Consulta técnica',
          estado: 'Abierto',
          prioridad: 'Media',
          created_at: '2026-01-14T11:00:00',
          assigned_at: '2026-01-14T11:02:00'
        }
      ]
      setMyTickets(mockTickets)

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

  useEffect(() => {
    if (personId) {
      fetchOperatorData()
      // Actualizar cada 30 segundos
      const interval = setInterval(fetchOperatorData, 30000)
      return () => clearInterval(interval)
    }
  }, [personId])

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

  const openTickets = myTickets.filter(t => t.estado === 'Abierto' || t.estado === 'En Progreso')
  const closedTickets = myTickets.filter(t => t.estado === 'Cerrado')

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
                {operatorData.whatsapp_enabled ? (
                  <span className="text-green-600">✅ Habilitadas</span>
                ) : (
                  <span className="text-gray-600">🔕 Deshabilitadas</span>
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

      {/* KPIs del Operador */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tickets Activos</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{openTickets.length}</div>
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
            <div className="text-2xl font-bold text-green-600">{closedTickets.length}</div>
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
            <CardTitle className="text-sm font-medium">Tiempo Promedio</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avg_response_time || 0} min</div>
            <p className="text-xs text-muted-foreground">
              Tiempo de respuesta
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
                const daySchedules = operatorData.schedules.filter(s => s.day_of_week === index)
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
          <CardTitle>Mis Tickets Asignados</CardTitle>
          <CardDescription>Tickets actualmente bajo tu responsabilidad</CardDescription>
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
                </tr>
              </thead>
              <tbody>
                {myTickets.length > 0 ? (
                  myTickets.map((ticket) => (
                    <tr key={ticket.id} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-mono text-xs">{ticket.ticket_id}</td>
                      <td className="p-2">{ticket.cliente}</td>
                      <td className="p-2 max-w-xs truncate">{ticket.asunto}</td>
                      <td className="p-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.estado === 'Cerrado' ? 'bg-green-100 text-green-800' :
                          ticket.estado === 'Abierto' ? 'bg-orange-100 text-orange-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {ticket.estado}
                        </span>
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
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-muted-foreground">
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
    </div>
  )
}
