import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Calendar, TrendingUp, Clock, AlertCircle, CheckCircle, Filter, Download, Search, Edit2, Trash2, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

export default function Metrics() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState(null)
  const [tickets, setTickets] = useState([])
  const [filteredTickets, setFilteredTickets] = useState([])
  const [filters, setFilters] = useState({
    startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    status: 'all',
    operator: 'all',
    priority: 'all'
  })
  const { toast } = useToast()

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getMetrics()
      setMetrics(response.data.metrics)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar métricas',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchTickets = async () => {
    try {
      // Obtener tickets desde la base de datos
      const response = await adminApi.getIncidents()
      const incidents = response.data.incidents || []
      
      // Transformar los datos al formato esperado
      const transformedTickets = incidents.map(incident => ({
        id: incident.id,
        ticket_id: incident.ticket_id,
        cliente: incident.customer_name || 'N/A',
        asunto: incident.subject || 'Sin asunto',
        estado: incident.status_name || 'Desconocido',
        prioridad: incident.priority_name || 'Media',
        assigned_to: incident.assigned_to,
        operator_name: incident.operator_name || 'Sin asignar',
        created_at: incident.created_at,
        response_time: incident.response_time_minutes,
        exceeded_threshold: incident.exceeded_threshold || false
      }))
      
      setTickets(transformedTickets)
      setFilteredTickets(transformedTickets)
    } catch (error) {
      console.error('Error al cargar tickets:', error)
      toast({
        title: 'Error',
        description: 'Error al cargar tickets',
        variant: 'destructive'
      })
    }
  }

  const handleToggleThreshold = async (ticketId, currentStatus) => {
    try {
      await adminApi.updateTicketThreshold(ticketId, { 
        exceeded_threshold: !currentStatus 
      })
      
      toast({
        title: 'Actualizado',
        description: `Ticket ${!currentStatus ? 'marcado como vencido' : 'desmarcado como vencido'}`,
      })
      
      // Recargar datos
      await fetchTickets()
      await fetchMetrics()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar el ticket',
        variant: 'destructive'
      })
    }
  }

  const handleDeleteTicket = async (ticketId) => {
    if (!confirm('¿Estás seguro de eliminar este ticket? Esta acción no se puede deshacer.')) {
      return
    }

    try {
      await adminApi.deleteTicket(ticketId)
      
      toast({
        title: 'Eliminado',
        description: 'Ticket eliminado correctamente',
      })
      
      // Recargar datos
      await fetchTickets()
      await fetchMetrics()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al eliminar el ticket',
        variant: 'destructive'
      })
    }
  }

  useEffect(() => {
    fetchMetrics()
    fetchTickets()
  }, [])

  // Función para parsear fecha en formato DD-MM-YYYY HH:MM:SS
  const parseDate = (dateStr) => {
    if (!dateStr) return null
    // Formato: "14-01-2026 21:41:31"
    const parts = dateStr.split(' ')
    const dateParts = parts[0].split('-')
    const timeParts = parts[1]?.split(':') || ['00', '00', '00']
    
    // Convertir a formato ISO: YYYY-MM-DD
    const year = dateParts[2]
    const month = dateParts[1]
    const day = dateParts[0]
    
    return new Date(`${year}-${month}-${day}T${timeParts.join(':')}`)
  }

  // No aplicar filtros automáticamente, solo cuando se haga clic en buscar
  const applyFilters = () => {
    let filtered = [...tickets]

    // Filtrar por fecha (manejar formato DD-MM-YYYY)
    if (filters.startDate) {
      const startDate = new Date(filters.startDate)
      filtered = filtered.filter(t => {
        const ticketDate = parseDate(t.created_at)
        return ticketDate && ticketDate >= startDate
      })
    }
    if (filters.endDate) {
      const endDate = new Date(filters.endDate + 'T23:59:59')
      filtered = filtered.filter(t => {
        const ticketDate = parseDate(t.created_at)
        return ticketDate && ticketDate <= endDate
      })
    }

    // Filtrar por estado
    if (filters.status !== 'all') {
      filtered = filtered.filter(t => t.estado === filters.status)
    }

    // Filtrar por operador
    if (filters.operator !== 'all') {
      filtered = filtered.filter(t => t.assigned_to === parseInt(filters.operator))
    }

    // Filtrar por prioridad
    if (filters.priority !== 'all') {
      filtered = filtered.filter(t => t.prioridad === filters.priority)
    }

    setFilteredTickets(filtered)
  }

  const exportToCSV = () => {
    const headers = ['ID', 'Cliente', 'Asunto', 'Estado', 'Prioridad', 'Operador', 'Fecha', 'Tiempo Respuesta']
    const rows = filteredTickets.map(t => [
      t.ticket_id,
      t.cliente,
      t.asunto,
      t.estado,
      t.prioridad,
      t.operator_name,
      new Date(t.created_at).toLocaleString(),
      t.response_time ? `${t.response_time} min` : 'N/A'
    ])

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tickets_${filters.startDate}_${filters.endDate}.csv`
    a.click()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  // Calcular distribución por operador dinámicamente desde tickets filtrados
  const operatorDistribution = {}
  filteredTickets.forEach(ticket => {
    const operatorId = ticket.assigned_to
    const operatorName = ticket.operator_name
    
    if (!operatorDistribution[operatorId]) {
      operatorDistribution[operatorId] = {
        name: operatorName,
        person_id: operatorId,
        assigned: 0,
        completed: 0,
        exceeded_threshold: 0,
        sla_percentage: 0
      }
    }
    
    operatorDistribution[operatorId].assigned++
    if (ticket.estado === 'SUCCESS') {
      operatorDistribution[operatorId].completed++
    }
    if (ticket.exceeded_threshold) {
      operatorDistribution[operatorId].exceeded_threshold++
    }
  })
  
  // Calcular SLA para cada operador
  Object.values(operatorDistribution).forEach(op => {
    if (op.assigned > 0) {
      const withinSLA = op.assigned - op.exceeded_threshold
      op.sla_percentage = ((withinSLA / op.assigned) * 100).toFixed(2)
    }
  })
  
  const operatorData = Object.values(operatorDistribution)
  
  // Calcular métricas dinámicamente basadas en tickets filtrados
  const filteredMetrics = {
    total: filteredTickets.length,
    open: filteredTickets.filter(t => !t.exceeded_threshold && t.estado !== 'SUCCESS').length,
    closed: filteredTickets.filter(t => t.estado === 'SUCCESS').length,
    overdue: filteredTickets.filter(t => t.exceeded_threshold).length,
    avgResponseTime: filteredTickets.length > 0 
      ? (filteredTickets.reduce((sum, t) => sum + (t.response_time || 0), 0) / filteredTickets.filter(t => t.response_time).length).toFixed(2)
      : 0
  }
  
  // Filtrar solo estados con valores > 0 para el gráfico (usar datos filtrados)
  const allStatusData = [
    { name: 'Cerrados', value: filteredMetrics.closed, color: '#00C49F' },
    { name: 'Abiertos', value: filteredMetrics.open, color: '#FF8042' },
    { name: 'Vencidos', value: filteredMetrics.overdue, color: '#FFBB28' }
  ]
  const statusData = allStatusData.filter(item => item.value > 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Métricas y Reportes</h1>
          <p className="text-muted-foreground">
            Análisis detallado de tickets y rendimiento del equipo
          </p>
        </div>
        <Button onClick={fetchMetrics} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros de Búsqueda
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="text-sm font-medium block mb-2">Fecha Inicio</label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                className="w-full px-3 py-2 border rounded-md text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Fecha Fin</label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                className="w-full px-3 py-2 border rounded-md text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Estado</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 border rounded-md text-sm"
              >
                <option value="all">Todos</option>
                <option value="Abierto">Abierto</option>
                <option value="En Progreso">En Progreso</option>
                <option value="Cerrado">Cerrado</option>
                <option value="Vencido">Vencido</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium block mb-2">Prioridad</label>
              <select
                value={filters.priority}
                onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
                className="w-full px-3 py-2 border rounded-md text-sm"
              >
                <option value="all">Todas</option>
                <option value="Alta">Alta</option>
                <option value="Media">Media</option>
                <option value="Baja">Baja</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={applyFilters} className="flex-1" variant="default">
                <Search className="h-4 w-4 mr-2" />
                Buscar
              </Button>
              <Button onClick={exportToCSV} className="flex-1" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Exportar CSV
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPIs - Usar métricas filtradas */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tickets</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredMetrics.total}</div>
            <p className="text-xs text-muted-foreground">
              En el sistema
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tickets Abiertos</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {filteredMetrics.open}
            </div>
            <p className="text-xs text-muted-foreground">
              Pendientes de asignación
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tickets Cerrados</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {filteredMetrics.closed}
            </div>
            <p className="text-xs text-muted-foreground">
              Resueltos exitosamente
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tiempo Promedio</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredMetrics.avgResponseTime} min
            </div>
            <p className="text-xs text-muted-foreground">
              Tiempo de respuesta
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Distribución por Operador */}
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Operador</CardTitle>
            <CardDescription>Tickets asignados a cada operador</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={operatorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="assigned" fill="#0088FE" name="Asignados" />
                <Bar dataKey="completed" fill="#00C49F" name="Completados" />
                <Bar dataKey="exceeded_threshold" fill="#FF8042" name="Vencidos" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribución por Estado */}
        <Card>
          <CardHeader>
            <CardTitle>Distribución por Estado</CardTitle>
            <CardDescription>Estado actual de los tickets</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Tabla de SLA por Operador */}
      <Card>
        <CardHeader>
          <CardTitle>SLA por Operador</CardTitle>
          <CardDescription>
            Porcentaje de cumplimiento de tiempo de respuesta por operador
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2 font-medium">Operador</th>
                  <th className="text-left p-2 font-medium">Total Tickets</th>
                  <th className="text-left p-2 font-medium">Completados</th>
                  <th className="text-left p-2 font-medium">Vencidos</th>
                  <th className="text-left p-2 font-medium">SLA %</th>
                </tr>
              </thead>
              <tbody>
                {operatorData.map((operator) => (
                  <tr key={operator.person_id} className="border-b hover:bg-gray-50">
                    <td className="p-2 font-medium">{operator.name}</td>
                    <td className="p-2">{operator.assigned}</td>
                    <td className="p-2 text-green-600">{operator.completed}</td>
                    <td className="p-2 text-red-600">{operator.exceeded_threshold || 0}</td>
                    <td className="p-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              operator.sla_percentage >= 95 ? 'bg-green-500' :
                              operator.sla_percentage >= 85 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${operator.sla_percentage || 100}%` }}
                          />
                        </div>
                        <span className="font-semibold min-w-[60px]">
                          {operator.sla_percentage || 100}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Tickets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Lista de Tickets ({filteredTickets.length})
          </CardTitle>
          <CardDescription>
            Tickets filtrados según los criterios seleccionados
          </CardDescription>
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
                  <th className="text-left p-2 font-medium">Operador</th>
                  <th className="text-left p-2 font-medium">Fecha</th>
                  <th className="text-left p-2 font-medium">Tiempo</th>
                  <th className="text-left p-2 font-medium">Vencido</th>
                  <th className="text-left p-2 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.length > 0 ? (
                  filteredTickets.map((ticket) => (
                    <tr key={ticket.id} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-mono text-xs">{ticket.ticket_id}</td>
                      <td className="p-2">{ticket.cliente}</td>
                      <td className="p-2 max-w-xs truncate">{ticket.asunto}</td>
                      <td className="p-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.estado === 'SUCCESS' ? 'bg-green-100 text-green-800' :
                          ticket.estado === 'FAIL' ? 'bg-red-100 text-red-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {ticket.estado}
                        </span>
                      </td>
                      <td className="p-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.prioridad === 'high' ? 'bg-red-100 text-red-800' :
                          ticket.prioridad === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {ticket.prioridad}
                        </span>
                      </td>
                      <td className="p-2">{ticket.operator_name || 'Sin asignar'}</td>
                      <td className="p-2 text-xs text-gray-600">
                        {ticket.created_at}
                      </td>
                      <td className="p-2 text-xs">
                        {ticket.response_time ? `${ticket.response_time} min` : 'N/A'}
                      </td>
                      <td className="p-2">
                        {ticket.exceeded_threshold ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Sí
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            No
                          </span>
                        )}
                      </td>
                      <td className="p-2">
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleToggleThreshold(ticket.ticket_id, ticket.exceeded_threshold)}
                            className="h-7 px-2"
                            title={ticket.exceeded_threshold ? 'Marcar como NO vencido' : 'Marcar como vencido'}
                          >
                            <Edit2 className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteTicket(ticket.ticket_id)}
                            className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                            title="Eliminar ticket"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="10" className="p-8 text-center text-muted-foreground">
                      No hay tickets que coincidan con los filtros
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Información sobre Métricas</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>• Las fechas se refieren al período de creación de los tickets</p>
          <p>• El tiempo promedio se calcula desde la creación hasta la primera respuesta</p>
          <p>• Los datos se actualizan en tiempo real</p>
          <p>• Puedes exportar los datos filtrados a CSV para análisis externo</p>
        </CardContent>
      </Card>
    </div>
  )
}
