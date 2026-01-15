import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Calendar, TrendingUp, Clock, AlertCircle, CheckCircle, Filter, Download, Search } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

export default function Metrics() {
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState(null)
  const [tickets, setTickets] = useState([])
  const [filteredTickets, setFilteredTickets] = useState([])
  const [filters, setFilters] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
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
      // Aquí deberías llamar a un endpoint que devuelva los tickets
      // Por ahora usamos datos de ejemplo
      const mockTickets = [
        {
          id: 1,
          ticket_id: 'T-001',
          cliente: 'Cliente A',
          asunto: 'Problema de conexión',
          estado: 'Abierto',
          prioridad: 'Alta',
          assigned_to: 1,
          operator_name: 'Luis Sarco',
          created_at: '2026-01-14T10:00:00',
          response_time: 15
        },
        // Más tickets...
      ]
      setTickets(mockTickets)
      setFilteredTickets(mockTickets)
    } catch (error) {
      console.error('Error al cargar tickets:', error)
    }
  }

  useEffect(() => {
    fetchMetrics()
    fetchTickets()
  }, [])

  useEffect(() => {
    applyFilters()
  }, [filters, tickets])

  const applyFilters = () => {
    let filtered = [...tickets]

    // Filtrar por fecha
    if (filters.startDate) {
      filtered = filtered.filter(t => new Date(t.created_at) >= new Date(filters.startDate))
    }
    if (filters.endDate) {
      filtered = filtered.filter(t => new Date(t.created_at) <= new Date(filters.endDate + 'T23:59:59'))
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

  const operatorData = metrics?.operator_distribution || []
  const statusData = [
    { name: 'Abiertos', value: metrics?.open_tickets || 0 },
    { name: 'En Progreso', value: metrics?.in_progress_tickets || 0 },
    { name: 'Cerrados', value: metrics?.closed_tickets || 0 },
    { name: 'Vencidos', value: metrics?.overdue_tickets || 0 }
  ]

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
            <div className="flex items-end">
              <Button onClick={exportToCSV} className="w-full">
                <Download className="h-4 w-4 mr-2" />
                Exportar CSV
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tickets</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredTickets.length}</div>
            <p className="text-xs text-muted-foreground">
              En el período seleccionado
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
              {filteredTickets.filter(t => t.estado === 'Abierto').length}
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
              {filteredTickets.filter(t => t.estado === 'Cerrado').length}
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
              {metrics?.average_response_time || 0} min
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
                          ticket.estado === 'Cerrado' ? 'bg-green-100 text-green-800' :
                          ticket.estado === 'Abierto' ? 'bg-orange-100 text-orange-800' :
                          ticket.estado === 'Vencido' ? 'bg-red-100 text-red-800' :
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
                      <td className="p-2">{ticket.operator_name || 'Sin asignar'}</td>
                      <td className="p-2 text-xs text-gray-600">
                        {new Date(ticket.created_at).toLocaleString()}
                      </td>
                      <td className="p-2 text-xs">
                        {ticket.response_time ? `${ticket.response_time} min` : 'N/A'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-muted-foreground">
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
