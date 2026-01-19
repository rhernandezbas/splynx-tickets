import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { deviceAnalysisApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { 
  Search, 
  Activity, 
  Wifi, 
  Signal, 
  Clock, 
  CheckCircle, 
  XCircle, 
  ThumbsUp, 
  ThumbsDown, 
  AlertTriangle,
  RefreshCw,
  History,
  BarChart3,
  Loader2,
  MessageSquare,
  TrendingUp,
  Server,
  Radio,
  FileText
} from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function DeviceAnalysis() {
  const [deviceIp, setDeviceIp] = useState('')
  const [sshUsername, setSshUsername] = useState('')
  const [sshPassword, setSshPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [currentAnalysisId, setCurrentAnalysisId] = useState(null)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [history, setHistory] = useState([])
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState([])
  const [logsStats, setLogsStats] = useState(null)
  const [logsLoading, setLogsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('analyze')
  const { toast } = useToast()

  const currentUser = JSON.parse(sessionStorage.getItem('user') || '{}')
  const username = currentUser.username || 'unknown'
  const userRole = currentUser.role || 'unknown'

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory()
    } else if (activeTab === 'stats') {
      fetchStats()
    } else if (activeTab === 'logs' && userRole === 'admin') {
      fetchLogs()
      fetchLogsStats()
    }
  }, [activeTab])

  const fetchHistory = async () => {
    try {
      const response = await deviceAnalysisApi.getHistory({ limit: 50 })
      setHistory(response.data.analyses || [])
    } catch (error) {
      console.error('Error fetching history:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await deviceAnalysisApi.getStats()
      setStats(response.data.stats || null)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const fetchLogs = async () => {
    setLogsLoading(true)
    try {
      const response = await deviceAnalysisApi.getApiLogs({
        limit: 100,
        requested_by_role: userRole
      })
      console.log('Logs response:', response.data)
      
      // La API devuelve logs como strings, necesitamos parsearlos
      const rawLogs = response.data.logs || []
      const parsedLogs = rawLogs.map(logString => {
        // Formato: "2026-01-19 01:47:36 [INFO] uvicorn.access:483 - mensaje"
        const match = logString.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARNING|ERROR|DEBUG)\] (.+)$/)
        
        if (match) {
          return {
            timestamp: match[1],
            level: match[2],
            message: match[3]
          }
        }
        
        // Si no coincide con el formato, devolver como está
        return {
          timestamp: '',
          level: 'INFO',
          message: logString
        }
      })
      
      setLogs(parsedLogs)
    } catch (error) {
      console.error('Error fetching logs:', error)
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al obtener logs de la API',
        variant: 'destructive'
      })
    } finally {
      setLogsLoading(false)
    }
  }

  const fetchLogsStats = async () => {
    try {
      // Obtener los logs para calcular estadísticas por nivel
      const response = await deviceAnalysisApi.getApiLogs({
        limit: 1000, // Obtener más logs para estadísticas precisas
        requested_by_role: userRole
      })
      console.log('Logs for stats response:', response.data)
      
      // Calcular estadísticas por nivel desde los logs
      const rawLogs = response.data.logs || []
      const levelCounts = { ERROR: 0, WARNING: 0, INFO: 0, DEBUG: 0 }
      
      rawLogs.forEach(logString => {
        if (logString.includes('[ERROR]')) levelCounts.ERROR++
        else if (logString.includes('[WARNING]')) levelCounts.WARNING++
        else if (logString.includes('[INFO]')) levelCounts.INFO++
        else if (logString.includes('[DEBUG]')) levelCounts.DEBUG++
      })
      
      // Obtener estadísticas generales de archivos
      const statsResponse = await deviceAnalysisApi.getApiLogsStats({
        requested_by_role: userRole
      })
      
      // Combinar estadísticas de archivos con conteos por nivel
      setLogsStats({
        ...statsResponse.data,
        total_lines_in_file: statsResponse.data.stats?.app?.total_lines || 0,
        total_size_mb: statsResponse.data.stats?.app?.size_mb || 0,
        lines_returned: rawLogs.length,
        by_level: levelCounts
      })
    } catch (error) {
      console.error('Error fetching logs stats:', error)
      // Si hay error, establecer valores por defecto
      setLogsStats({
        total_lines_in_file: 0,
        total_size_mb: 0,
        lines_returned: 0,
        by_level: {
          ERROR: 0,
          WARNING: 0,
          INFO: 0,
          DEBUG: 0
        }
      })
    }
  }

  const handleAnalyzeComplete = async () => {
    if (!deviceIp.trim()) {
      toast({
        title: 'Error',
        description: 'Por favor ingresa una dirección IP',
        variant: 'destructive'
      })
      return
    }

    setLoading(true)
    setAnalysisResult(null)
    setCurrentAnalysisId(null)
    setFeedbackSubmitted(false)
    setFeedbackComment('')

    try {
      const payload = {
        ip_address: deviceIp.trim(),
        requested_by: username,
        requested_by_role: userRole
      }

      if (sshUsername.trim()) {
        payload.ssh_username = sshUsername.trim()
      }
      if (sshPassword.trim()) {
        payload.ssh_password = sshPassword.trim()
      }

      const response = await deviceAnalysisApi.analyzeComplete(payload)
      
      setAnalysisResult(response.data)
      setCurrentAnalysisId(response.data.analysis_id)

      if (response.data.success) {
        toast({
          title: 'Análisis Completo',
          description: `Dispositivo ${response.data.device?.name || deviceIp} analizado exitosamente`,
        })
      } else {
        toast({
          title: 'Análisis con Errores',
          description: response.data.detail || 'El análisis se completó con errores',
          variant: 'destructive'
        })
      }
    } catch (error) {
      console.error('Error analyzing device:', error)
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al analizar el dispositivo',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleGetMetrics = async () => {
    if (!deviceIp.trim()) {
      toast({
        title: 'Error',
        description: 'Por favor ingresa una dirección IP',
        variant: 'destructive'
      })
      return
    }

    setLoading(true)
    setAnalysisResult(null)
    setCurrentAnalysisId(null)
    setFeedbackSubmitted(false)
    setFeedbackComment('')

    try {
      const response = await deviceAnalysisApi.getMetrics({
        ip_address: deviceIp.trim(),
        requested_by: username,
        requested_by_role: userRole
      })

      setAnalysisResult(response.data)
      setCurrentAnalysisId(response.data.analysis_id)

      toast({
        title: 'Métricas Obtenidas',
        description: `Métricas del dispositivo ${response.data.device_name || deviceIp} obtenidas`,
      })
    } catch (error) {
      console.error('Error getting metrics:', error)
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al obtener métricas',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitFeedback = async (rating) => {
    if (!currentAnalysisId) {
      toast({
        title: 'Error',
        description: 'No hay análisis para calificar',
        variant: 'destructive'
      })
      return
    }

    try {
      await deviceAnalysisApi.submitFeedback(currentAnalysisId, {
        rating,
        comment: feedbackComment.trim()
      })

      setFeedbackSubmitted(true)
      toast({
        title: 'Feedback Enviado',
        description: 'Gracias por tu feedback',
      })
    } catch (error) {
      console.error('Error submitting feedback:', error)
      toast({
        title: 'Error',
        description: 'Error al enviar feedback',
        variant: 'destructive'
      })
    }
  }

  const renderLLMSummary = (summary) => {
    if (!summary) return null

    const sections = summary.split(/\n\n+/)
    
    return (
      <div className="space-y-4">
        {sections.map((section, idx) => {
          const lines = section.split('\n').filter(line => line.trim())
          return (
            <div key={idx} className="bg-slate-50 p-4 rounded-lg">
              {lines.map((line, lineIdx) => {
                const isHeader = line.match(/^[0-9]️⃣/)
                return (
                  <p 
                    key={lineIdx} 
                    className={isHeader ? 'font-bold text-lg mb-2 text-blue-700' : 'ml-4 text-sm'}
                  >
                    {line}
                  </p>
                )
              })}
            </div>
          )
        })}
      </div>
    )
  }

  const renderPingData = (ping) => {
    if (!ping) return null

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="flex items-center gap-2">
          {ping.reachable ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
          <div>
            <p className="text-xs text-gray-500">Estado</p>
            <p className="font-semibold">{ping.reachable ? 'Alcanzable' : 'No Alcanzable'}</p>
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500">Latencia Promedio</p>
          <p className="font-semibold">{ping.avg_latency_ms?.toFixed(2) || 'N/A'} ms</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Pérdida de Paquetes</p>
          <p className="font-semibold">{ping.packet_loss?.toFixed(1) || 0}%</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Paquetes</p>
          <p className="font-semibold">{ping.packets_received || 0}/{ping.packets_sent || 0}</p>
        </div>
      </div>
    )
  }

  const renderMetrics = (metrics) => {
    if (!metrics) return null

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Signal className="h-4 w-4" />
                Señal
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{metrics.signal?.current || 'N/A'} dBm</p>
              <p className="text-xs text-gray-500">Max: {metrics.signal?.max || 'N/A'} dBm</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Activity className="h-4 w-4" />
                CPU / RAM
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{metrics.cpu || 'N/A'}% / {metrics.ram || 'N/A'}%</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Uptime
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-semibold">{metrics.uptime?.formatted || 'N/A'}</p>
            </CardContent>
          </Card>
        </div>

        {metrics.wireless && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Wifi className="h-4 w-4" />
                Wireless
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">SSID</p>
                  <p className="font-semibold">{metrics.wireless.ssid || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-gray-500">Frecuencia</p>
                  <p className="font-semibold">{metrics.wireless.frequency || 'N/A'} MHz</p>
                </div>
                <div>
                  <p className="text-gray-500">TX/RX</p>
                  <p className="font-semibold">{metrics.wireless.tx_rate || 'N/A'} / {metrics.wireless.rx_rate || 'N/A'} Mbps</p>
                </div>
                <div>
                  <p className="text-gray-500">Clientes</p>
                  <p className="font-semibold">{metrics.wireless.client_count || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {metrics.ethernet && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Server className="h-4 w-4" />
                Ethernet
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{metrics.ethernet.speed || 'N/A'}</p>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  const renderSiteSurvey = (siteSurvey) => {
    if (!siteSurvey || !siteSurvey.alternative_aps) return null

    return (
      <div className="space-y-2">
        <h4 className="font-semibold text-sm mb-2">APs Alternativos Disponibles</h4>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {siteSurvey.alternative_aps.map((ap, idx) => (
            <div key={idx} className="bg-slate-50 p-3 rounded-lg flex items-center justify-between">
              <div className="flex-1">
                <p className="font-semibold text-sm">{ap.ssid || 'Unknown'}</p>
                <p className="text-xs text-gray-500">MAC: {ap.bssid || ap.mac || 'N/A'}</p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-xs text-gray-500">Señal</p>
                  <p className="font-semibold text-sm">{ap.signal || 'N/A'} dBm</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Clientes</p>
                  <p className="font-semibold text-sm">{ap.client_count || 0}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Frecuencia</p>
                  <p className="font-semibold text-sm">{ap.frequency || 'N/A'} MHz</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Análisis de Dispositivos</h1>
          <p className="text-gray-500">Análisis completo de dispositivos Ubiquiti con IA</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="analyze" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Analizar
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Historial
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Estadísticas
          </TabsTrigger>
          {userRole === 'admin' && (
            <TabsTrigger value="logs" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Logs API
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="analyze" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Consultar Dispositivo</CardTitle>
              <CardDescription>
                Ingresa la IP del dispositivo para realizar un análisis completo o solo obtener métricas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="deviceIp">Dirección IP *</Label>
                  <Input
                    id="deviceIp"
                    placeholder="100.64.12.94"
                    value={deviceIp}
                    onChange={(e) => setDeviceIp(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sshUsername">Usuario SSH (opcional)</Label>
                  <Input
                    id="sshUsername"
                    placeholder="ubnt"
                    value={sshUsername}
                    onChange={(e) => setSshUsername(e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="sshPassword">Password SSH (opcional)</Label>
                  <Input
                    id="sshPassword"
                    type="password"
                    placeholder="••••••••"
                    value={sshPassword}
                    onChange={(e) => setSshPassword(e.target.value)}
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <Button 
                  onClick={handleAnalyzeComplete} 
                  disabled={loading}
                  className="flex items-center gap-2"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Radio className="h-4 w-4" />
                  )}
                  Análisis Completo (con IA)
                </Button>
                <Button 
                  onClick={handleGetMetrics} 
                  disabled={loading}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Activity className="h-4 w-4" />
                  )}
                  Solo Métricas
                </Button>
              </div>

              {loading && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-700 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analizando dispositivo... Esto puede tomar hasta 2 minutos
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {analysisResult && (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {analysisResult.success ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                        Resultado del Análisis
                      </CardTitle>
                      <CardDescription>
                        {analysisResult.device?.name && `${analysisResult.device.name} - `}
                        {analysisResult.device?.model || analysisResult.device_model || 'Dispositivo'}
                        {' • IP: '}{analysisResult.device?.ip || deviceIp}
                      </CardDescription>
                    </div>
                    <div className="text-right text-sm text-gray-500">
                      <p>Tiempo: {analysisResult.execution_time_ms}ms</p>
                      <p>ID: {currentAnalysisId}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {!analysisResult.success && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="text-sm text-red-700 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        {analysisResult.detail || analysisResult.error || 'Error desconocido'}
                      </p>
                    </div>
                  )}

                  {analysisResult.analysis?.llm_summary && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Análisis IA
                      </h3>
                      {renderLLMSummary(analysisResult.analysis.llm_summary)}
                    </div>
                  )}

                  {analysisResult.analysis?.ping && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Conectividad (Ping)</h3>
                      {renderPingData(analysisResult.analysis.ping)}
                    </div>
                  )}

                  {(analysisResult.analysis?.metrics || analysisResult.device_name) && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Métricas del Dispositivo</h3>
                      {renderMetrics(analysisResult.analysis?.metrics || analysisResult)}
                    </div>
                  )}

                  {analysisResult.analysis?.site_survey && (
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Site Survey</h3>
                      {renderSiteSurvey(analysisResult.analysis.site_survey)}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Feedback
                  </CardTitle>
                  <CardDescription>
                    ¿Fue útil este análisis? Tu feedback nos ayuda a mejorar
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!feedbackSubmitted ? (
                    <>
                      <div className="flex gap-3">
                        <Button
                          onClick={() => handleSubmitFeedback('helpful')}
                          variant="outline"
                          className="flex items-center gap-2"
                        >
                          <ThumbsUp className="h-4 w-4" />
                          Útil
                        </Button>
                        <Button
                          onClick={() => handleSubmitFeedback('not_helpful')}
                          variant="outline"
                          className="flex items-center gap-2"
                        >
                          <ThumbsDown className="h-4 w-4" />
                          No útil
                        </Button>
                        <Button
                          onClick={() => handleSubmitFeedback('incorrect')}
                          variant="outline"
                          className="flex items-center gap-2"
                        >
                          <AlertTriangle className="h-4 w-4" />
                          Incorrecto
                        </Button>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="feedbackComment">Comentario (opcional)</Label>
                        <Textarea
                          id="feedbackComment"
                          placeholder="Cuéntanos más sobre tu experiencia..."
                          value={feedbackComment}
                          onChange={(e) => setFeedbackComment(e.target.value)}
                          rows={3}
                        />
                      </div>
                    </>
                  ) : (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="text-sm text-green-700 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" />
                        ¡Gracias por tu feedback!
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Historial de Análisis</CardTitle>
                <CardDescription>Últimos 50 análisis realizados</CardDescription>
              </div>
              <Button onClick={fetchHistory} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {history.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No hay análisis previos</p>
                ) : (
                  history.map((item) => (
                    <div
                      key={item.id}
                      className="border rounded-lg p-4 hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            {item.success ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500" />
                            )}
                            <span className="font-semibold">
                              {item.device_name || item.device_ip}
                            </span>
                            {item.device_model && (
                              <span className="text-sm text-gray-500">({item.device_model})</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <p>IP: {item.device_ip}</p>
                            <p>Tipo: {item.analysis_type === 'complete' ? 'Completo' : 'Métricas'}</p>
                            <p>Por: {item.requested_by} ({item.requested_by_role})</p>
                            <p>Fecha: {new Date(item.requested_at).toLocaleString('es-ES')}</p>
                            {item.feedback_rating && (
                              <p className="flex items-center gap-1">
                                Feedback: 
                                {item.feedback_rating === 'helpful' && <ThumbsUp className="h-3 w-3 text-green-500" />}
                                {item.feedback_rating === 'not_helpful' && <ThumbsDown className="h-3 w-3 text-orange-500" />}
                                {item.feedback_rating === 'incorrect' && <AlertTriangle className="h-3 w-3 text-red-500" />}
                                <span className="capitalize">{item.feedback_rating.replace('_', ' ')}</span>
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="text-right text-sm">
                          <p className="text-gray-500">{item.execution_time_ms}ms</p>
                        </div>
                      </div>
                      {item.error_message && (
                        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                          {item.error_message}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Estadísticas Generales</CardTitle>
                <CardDescription>Métricas de uso del sistema de análisis</CardDescription>
              </div>
              <Button onClick={fetchStats} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent>
              {!stats ? (
                <p className="text-center text-gray-500 py-8">Cargando estadísticas...</p>
              ) : (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Total Análisis</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-3xl font-bold">{stats.total_analyses}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Exitosos</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-3xl font-bold text-green-600">{stats.successful_analyses}</p>
                        <p className="text-xs text-gray-500">{stats.success_rate}% éxito</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Fallidos</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-3xl font-bold text-red-600">{stats.failed_analyses}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Tiempo Promedio</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-3xl font-bold">{Number(stats.avg_execution_time_ms || 0).toFixed(0)}</p>
                        <p className="text-xs text-gray-500">milisegundos</p>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">Feedback</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm">Total con feedback:</span>
                          <span className="font-semibold">{stats.feedback.total_with_feedback}</span>
                        </div>
                        <div className="flex justify-between text-green-600">
                          <span className="text-sm flex items-center gap-1">
                            <ThumbsUp className="h-3 w-3" /> Útil:
                          </span>
                          <span className="font-semibold">{stats.feedback.helpful}</span>
                        </div>
                        <div className="flex justify-between text-orange-600">
                          <span className="text-sm flex items-center gap-1">
                            <ThumbsDown className="h-3 w-3" /> No útil:
                          </span>
                          <span className="font-semibold">{stats.feedback.not_helpful}</span>
                        </div>
                        <div className="flex justify-between text-red-600">
                          <span className="text-sm flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3" /> Incorrecto:
                          </span>
                          <span className="font-semibold">{stats.feedback.incorrect}</span>
                        </div>
                        <div className="pt-2 border-t">
                          <div className="flex justify-between">
                            <span className="text-sm">Tasa de feedback:</span>
                            <span className="font-semibold">{stats.feedback.feedback_rate}%</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">Por Tipo</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm">Análisis Completo:</span>
                          <span className="font-semibold">{stats.by_type.complete}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm">Solo Métricas:</span>
                          <span className="font-semibold">{stats.by_type.metrics}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Logs de la API de Ubiquiti</CardTitle>
                <CardDescription>Últimos 100 logs del sistema de análisis</CardDescription>
              </div>
              <Button onClick={() => { fetchLogs(); fetchLogsStats(); }} variant="outline" size="sm" disabled={logsLoading}>
                {logsLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              </Button>
            </CardHeader>
            <CardContent>
              {logsStats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Total Logs</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">{logsStats.total_lines_in_file || logsStats.lines_returned || 0}</p>
                      <p className="text-xs text-gray-500">{(logsStats.total_size_mb || 0).toFixed(2)} MB</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm text-red-600">Errores</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-red-600">{logsStats.by_level?.ERROR || 0}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm text-yellow-600">Warnings</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-yellow-600">{logsStats.by_level?.WARNING || 0}</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm text-blue-600">Info</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-blue-600">{logsStats.by_level?.INFO || 0}</p>
                    </CardContent>
                  </Card>
                </div>
              )}

              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {logsLoading ? (
                  <p className="text-center text-gray-500 py-8">Cargando logs...</p>
                ) : logs.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No hay logs disponibles</p>
                ) : (
                  logs.map((log, idx) => (
                    <div
                      key={idx}
                      className={`border rounded-lg p-3 text-sm font-mono ${
                        log.level === 'ERROR' ? 'bg-red-50 border-red-200' :
                        log.level === 'WARNING' ? 'bg-yellow-50 border-yellow-200' :
                        log.level === 'INFO' ? 'bg-blue-50 border-blue-200' :
                        'bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                              log.level === 'ERROR' ? 'bg-red-200 text-red-800' :
                              log.level === 'WARNING' ? 'bg-yellow-200 text-yellow-800' :
                              log.level === 'INFO' ? 'bg-blue-200 text-blue-800' :
                              'bg-gray-200 text-gray-800'
                            }`}>
                              {log.level}
                            </span>
                            <span className="text-xs text-gray-500">{log.timestamp}</span>
                          </div>
                          <p className="text-gray-800 break-words">{log.message}</p>
                          {log.details && (
                            <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-x-auto">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
