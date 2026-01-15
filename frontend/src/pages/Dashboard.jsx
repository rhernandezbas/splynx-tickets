import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi, systemApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { 
  Users, 
  UserCheck, 
  UserX, 
  Ticket, 
  Clock, 
  AlertTriangle,
  RefreshCw,
  Play,
  Pause
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [systemStatus, setSystemStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const fetchData = async () => {
    try {
      setLoading(true)
      const [statsRes, statusRes] = await Promise.all([
        adminApi.getDashboardStats(),
        systemApi.getStatus()
      ])
      setStats(statsRes.data.stats)
      setSystemStatus(statusRes.data.status)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar estadísticas',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleSystemToggle = async () => {
    try {
      if (systemStatus?.paused) {
        await systemApi.resume({ resumed_by: 'admin' })
        toast({
          title: 'Sistema Reanudado',
          description: 'El sistema ha sido reanudado exitosamente'
        })
      } else {
        await systemApi.pause({ 
          reason: 'Pausa manual desde panel admin',
          paused_by: 'admin'
        })
        toast({
          title: 'Sistema Pausado',
          description: 'El sistema ha sido pausado exitosamente'
        })
      }
      fetchData()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cambiar estado del sistema',
        variant: 'destructive'
      })
    }
  }

  const handleResetCounters = async () => {
    if (!confirm('¿Estás seguro de reiniciar todos los contadores de asignación?')) return
    
    try {
      await adminApi.resetCounters({ performed_by: 'admin' })
      toast({
        title: 'Contadores Reiniciados',
        description: 'Los contadores de round-robin han sido reiniciados'
      })
      fetchData()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al reiniciar contadores',
        variant: 'destructive'
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const chartData = stats?.operator_stats?.map(op => ({
    name: op.name,
    asignados: op.current_assignments,
    total: op.total_handled,
    pendientes: op.unresolved
  })) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Vista general del sistema de tickets
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
          <Button 
            onClick={handleSystemToggle}
            variant={systemStatus?.paused ? "default" : "destructive"}
            size="sm"
          >
            {systemStatus?.paused ? (
              <>
                <Play className="h-4 w-4 mr-2" />
                Reanudar Sistema
              </>
            ) : (
              <>
                <Pause className="h-4 w-4 mr-2" />
                Pausar Sistema
              </>
            )}
          </Button>
        </div>
      </div>

      {/* System Status Alert */}
      {systemStatus?.paused && (
        <Card className="border-yellow-500 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-yellow-800 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Sistema Pausado
            </CardTitle>
            <CardDescription className="text-yellow-700">
              {systemStatus.paused_reason || 'El sistema está pausado'}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Operadores
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.operators?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.operators?.active || 0} activos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Operadores Activos
            </CardTitle>
            <UserCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats?.operators?.active || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Trabajando actualmente
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Operadores Pausados
            </CardTitle>
            <UserX className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {stats?.operators?.paused || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Temporalmente inactivos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Asignaciones Totales
            </CardTitle>
            <Ticket className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.assignments?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.assignments?.today || 0} hoy
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tickets Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Tickets Sin Resolver
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {stats?.tickets?.unresolved || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Tickets pendientes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Tickets Vencidos
            </CardTitle>
            <Clock className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats?.tickets?.overdue || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Superan umbral de tiempo
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Tiempo Promedio
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.tickets?.avg_response_time_minutes?.toFixed(1) || 0} min
            </div>
            <p className="text-xs text-muted-foreground">
              Tiempo de respuesta
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Operators Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Distribución de Tickets por Operador</CardTitle>
              <CardDescription>
                Asignaciones actuales y totales manejadas
              </CardDescription>
            </div>
            <Button onClick={handleResetCounters} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reiniciar Contadores
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="asignados" fill="#3b82f6" name="Asignados Actuales" />
              <Bar dataKey="pendientes" fill="#f59e0b" name="Pendientes" />
              <Bar dataKey="total" fill="#10b981" name="Total Manejados" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Operator Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detalle de Operadores</CardTitle>
          <CardDescription>
            Estado actual y métricas de cada operador
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Operador</th>
                  <th className="text-left py-3 px-4">Estado</th>
                  <th className="text-right py-3 px-4">Asignados</th>
                  <th className="text-right py-3 px-4">Total</th>
                  <th className="text-right py-3 px-4">Pendientes</th>
                  <th className="text-right py-3 px-4">Tiempo Prom.</th>
                </tr>
              </thead>
              <tbody>
                {stats?.operator_stats?.map((op) => (
                  <tr key={op.person_id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{op.name}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        op.is_paused 
                          ? 'bg-orange-100 text-orange-800'
                          : op.is_active 
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {op.is_paused ? 'Pausado' : op.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">{op.current_assignments}</td>
                    <td className="py-3 px-4 text-right">{op.total_handled}</td>
                    <td className="py-3 px-4 text-right">{op.unresolved}</td>
                    <td className="py-3 px-4 text-right">
                      {op.avg_response_time?.toFixed(1) || 0} min
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
