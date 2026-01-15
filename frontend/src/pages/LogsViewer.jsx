import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { logsApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Search, Trash2, AlertCircle, Info, AlertTriangle, XCircle, CheckCircle, Filter, Download } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export default function LogsViewer() {
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    level: 'all',
    search: '',
    hours: 24,
    limit: 500
  })
  const [autoRefresh, setAutoRefresh] = useState(false)
  const { toast } = useToast()

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const response = await logsApi.getLogs(filters)
      setLogs(response.data.logs || [])
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar logs',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await logsApi.getStats({ hours: filters.hours })
      setStats(response.data.stats)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const handleClearLogs = async () => {
    if (!confirm('¿Estás seguro de eliminar todos los logs? Esta acción no se puede deshacer.')) {
      return
    }

    try {
      await logsApi.clearLogs()
      toast({
        title: 'Logs eliminados',
        description: 'Todos los logs han sido eliminados correctamente'
      })
      fetchLogs()
      fetchStats()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al eliminar logs',
        variant: 'destructive'
      })
    }
  }

  const exportLogs = () => {
    const headers = ['Timestamp', 'Level', 'Logger', 'Message']
    const rows = logs.map(log => [
      log.timestamp,
      log.level,
      log.logger,
      log.message
    ])

    const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${new Date().toISOString()}.csv`
    a.click()
  }

  useEffect(() => {
    fetchLogs()
    fetchStats()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchLogs()
      fetchStats()
    }, 5000)

    return () => clearInterval(interval)
  }, [autoRefresh, filters])

  const getLevelIcon = (level) => {
    switch (level) {
      case 'ERROR':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'INFO':
        return <Info className="h-4 w-4 text-blue-600" />
      case 'DEBUG':
        return <CheckCircle className="h-4 w-4 text-gray-600" />
      default:
        return <AlertCircle className="h-4 w-4" />
    }
  }

  const getLevelBadge = (level) => {
    const variants = {
      ERROR: 'destructive',
      WARNING: 'warning',
      INFO: 'default',
      DEBUG: 'secondary'
    }
    return (
      <Badge variant={variants[level] || 'default'} className="font-mono text-xs">
        {level}
      </Badge>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Logs</h1>
          <p className="text-muted-foreground">Visualiza y filtra los logs del sistema</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </Button>
          <Button variant="outline" onClick={exportLogs}>
            <Download className="h-4 w-4 mr-2" />
            Exportar CSV
          </Button>
          <Button variant="destructive" onClick={handleClearLogs}>
            <Trash2 className="h-4 w-4 mr-2" />
            Limpiar Logs
          </Button>
        </div>
      </div>

      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Logs</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">Últimas {filters.hours}h</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Errores</CardTitle>
              <XCircle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.by_level.ERROR || 0}</div>
              <p className="text-xs text-muted-foreground">Requieren atención</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Warnings</CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{stats.by_level.WARNING || 0}</div>
              <p className="text-xs text-muted-foreground">Advertencias</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Info</CardTitle>
              <Info className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.by_level.INFO || 0}</div>
              <p className="text-xs text-muted-foreground">Información</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Debug</CardTitle>
              <CheckCircle className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-600">{stats.by_level.DEBUG || 0}</div>
              <p className="text-xs text-muted-foreground">Depuración</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Nivel</label>
              <select
                className="w-full p-2 border rounded-md"
                value={filters.level}
                onChange={(e) => setFilters({ ...filters, level: e.target.value })}
              >
                <option value="all">Todos</option>
                <option value="ERROR">ERROR</option>
                <option value="WARNING">WARNING</option>
                <option value="INFO">INFO</option>
                <option value="DEBUG">DEBUG</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Período</label>
              <select
                className="w-full p-2 border rounded-md"
                value={filters.hours}
                onChange={(e) => setFilters({ ...filters, hours: parseInt(e.target.value) })}
              >
                <option value="1">Última hora</option>
                <option value="6">Últimas 6 horas</option>
                <option value="24">Últimas 24 horas</option>
                <option value="72">Últimos 3 días</option>
                <option value="168">Última semana</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Límite</label>
              <select
                className="w-full p-2 border rounded-md"
                value={filters.limit}
                onChange={(e) => setFilters({ ...filters, limit: parseInt(e.target.value) })}
              >
                <option value="100">100 logs</option>
                <option value="500">500 logs</option>
                <option value="1000">1000 logs</option>
                <option value="5000">5000 logs</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Buscar</label>
              <div className="flex gap-2">
                <Input
                  placeholder="Buscar en logs..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                />
                <Button onClick={fetchLogs}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Logs ({logs.length})</CardTitle>
          <CardDescription>
            Mostrando los últimos {logs.length} logs
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <RefreshCw className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No se encontraron logs con los filtros aplicados</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {getLevelIcon(log.level)}
                  </div>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {getLevelBadge(log.level)}
                      <span className="text-xs text-muted-foreground font-mono">
                        {log.timestamp}
                      </span>
                      <Badge variant="outline" className="text-xs font-mono">
                        {log.logger}
                      </Badge>
                    </div>
                    <p className="text-sm break-words font-mono">{log.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
