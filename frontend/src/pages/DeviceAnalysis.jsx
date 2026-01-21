import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
  FileText,
  Zap,
  Settings,
  Power,
  Star
} from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

// Station Analyzer Class
class StationAnalyzer {
  constructor(baseUrl = 'http://190.7.234.37:7657/api/v1') {
    this.baseUrl = baseUrl
  }

  async analyzeStation(ip, mac) {
    const response = await fetch(`${this.baseUrl}/stations/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ip,
        mac,
        username: 'ubnt',
        password: 'B8d7f9ub1234!'
      })
    })
    
    if (!response.ok) {
      throw new Error(`Error en análisis: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async enableFrequencies(ip, model) {
    const response = await fetch(`${this.baseUrl}/stations/enable-frequencies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, model })
    })
    
    if (!response.ok) {
      throw new Error(`Error habilitando frecuencias: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async waitForConnection(ip, maxWaitTime = 360) {
    const response = await fetch(`${this.baseUrl}/stations/wait-for-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip, max_wait_time: maxWaitTime })
    })
    
    if (!response.ok) {
      throw new Error(`Error esperando conexión: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async getFlowStatus(ip) {
    const response = await fetch(`${this.baseUrl}/stations/flow-status/${ip}`)
    
    if (!response.ok) {
      throw new Error(`Error obteniendo estado: ${response.statusText}`)
    }
    
    return await response.json()
  }

  // Feedback Endpoints
  async submitFeedback(analysisId, feedbackData) {
    const response = await fetch(`${this.baseUrl}/feedback/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis_id: analysisId,
        ...feedbackData
      })
    })
    
    if (!response.ok) {
      throw new Error(`Error enviando feedback: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async getFeedbackList() {
    const response = await fetch(`${this.baseUrl}/feedback/list`)
    
    if (!response.ok) {
      throw new Error(`Error obteniendo feedback: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async getFeedbackByAnalysis(analysisId) {
    const response = await fetch(`${this.baseUrl}/feedback/analysis/${analysisId}/feedback`)
    
    if (!response.ok) {
      throw new Error(`Error obteniendo feedback del análisis: ${response.statusText}`)
    }
    
    return await response.json()
  }

  // Logs Endpoints
  async getLogs(filters = {}) {
    const params = new URLSearchParams(filters)
    const response = await fetch(`${this.baseUrl}/logs/?${params}`)
    
    if (!response.ok) {
      throw new Error(`Error obteniendo logs: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async getRecentLogs(limit = 50) {
    const response = await fetch(`${this.baseUrl}/logs/recent?limit=${limit}`)
    
    if (!response.ok) {
      throw new Error(`Error obteniendo logs recientes: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async searchLogs(query, filters = {}) {
    const params = new URLSearchParams({ q: query, ...filters })
    const response = await fetch(`${this.baseUrl}/logs/search?${params}`)
    
    if (!response.ok) {
      throw new Error(`Error buscando logs: ${response.statusText}`)
    }
    
    return await response.json()
  }

  async clearLogs() {
    const response = await fetch(`${this.baseUrl}/logs/clear`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`Error limpiando logs: ${response.statusText}`)
    }
    
    return await response.json()
  }
}

export default function DeviceAnalysis() {
  const [deviceIp, setDeviceIp] = useState('')
  const [deviceMac, setDeviceMac] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [currentStep, setCurrentStep] = useState('idle') // idle, analyzing, frequency_prompt, enabling_frequencies, waiting_connection, completed
  const [progress, setProgress] = useState({})
  const [feedbackComment, setFeedbackComment] = useState('')
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [history, setHistory] = useState([])
  const [activeTab, setActiveTab] = useState('analyze')
  
  // Logs states
  const [logs, setLogs] = useState([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logsSearchQuery, setLogsSearchQuery] = useState('')
  const [logsFilters, setLogsFilters] = useState({
    level: '',
    limit: 100
  })
  
  // Feedback states
  const [feedbackList, setFeedbackList] = useState([])
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  
  const { toast } = useToast()

  const analyzer = new StationAnalyzer()

  useEffect(() => {
    if (activeTab === 'history') {
      fetchHistory()
    } else if (activeTab === 'logs') {
      fetchLogs()
    } else if (activeTab === 'feedback') {
      fetchFeedbackList()
    }
  }, [activeTab])

  const fetchHistory = async () => {
    try {
      // Por ahora simulamos historia local
      const savedHistory = localStorage.getItem('stationAnalysisHistory')
      if (savedHistory) {
        setHistory(JSON.parse(savedHistory))
      }
    } catch (error) {
      console.error('Error fetching history:', error)
    }
  }

  const saveToHistory = (analysis) => {
    const newEntry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ip: analysis.ip,
      model: analysis.identified_model,
      status: analysis.status,
      llm_analysis: analysis.llm_analysis
    }
    
    const updatedHistory = [newEntry, ...history.slice(0, 49)] // Keep last 50
    setHistory(updatedHistory)
    localStorage.setItem('stationAnalysisHistory', JSON.stringify(updatedHistory))
  }

  // Logs functions
  const fetchLogs = async () => {
    setLogsLoading(true)
    try {
      const response = await analyzer.getLogs(logsFilters)
      setLogs(response.data.logs || [])
    } catch (error) {
      console.error('Error fetching logs:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
    } finally {
      setLogsLoading(false)
    }
  }

  const fetchRecentLogs = async () => {
    setLogsLoading(true)
    try {
      const response = await analyzer.getRecentLogs(50)
      setLogs(response.data.logs || [])
    } catch (error) {
      console.error('Error fetching recent logs:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
    } finally {
      setLogsLoading(false)
    }
  }

  const searchLogs = async () => {
    if (!logsSearchQuery.trim()) {
      fetchLogs()
      return
    }
    
    setLogsLoading(true)
    try {
      const response = await analyzer.searchLogs(logsSearchQuery, logsFilters)
      setLogs(response.data.logs || [])
    } catch (error) {
      console.error('Error searching logs:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
    } finally {
      setLogsLoading(false)
    }
  }

  const clearLogs = async () => {
    try {
      await analyzer.clearLogs()
      setLogs([])
      toast({
        title: 'Logs Limpiados',
        description: 'Todos los logs han sido eliminados'
      })
    } catch (error) {
      console.error('Error clearing logs:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
    }
  }

  // Feedback functions
  const fetchFeedbackList = async () => {
    setFeedbackLoading(true)
    try {
      const response = await analyzer.getFeedbackList()
      setFeedbackList(response.data.feedback || [])
    } catch (error) {
      console.error('Error fetching feedback list:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
    } finally {
      setFeedbackLoading(false)
    }
  }

  const handleFeedback = async () => {
    if (!feedbackComment.trim()) {
      toast({
        title: 'Error',
        description: 'Por favor ingresa un comentario',
        variant: 'destructive'
      })
      return
    }

    try {
      // Enviar feedback a la API
      const feedbackData = {
        comment: feedbackComment,
        rating: 5, // Podrías agregar un selector de rating
        user_agent: navigator.userAgent,
        timestamp: new Date().toISOString()
      }

      if (analysisResult) {
        // Si hay un análisis actual, asociar el feedback
        await analyzer.submitFeedback(analysisResult.id || Date.now(), feedbackData)
      }

      setFeedbackSubmitted(true)
      toast({
        title: 'Gracias',
        description: 'Tu feedback ha sido enviado'
      })
      
      // Actualizar lista de feedback si estamos en esa tab
      if (activeTab === 'feedback') {
        fetchFeedbackList()
      }
    } catch (error) {
      console.error('Error sending feedback:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
    }
  }

  const handleAnalyze = async () => {
    if (!deviceIp) {
      toast({
        title: 'Error',
        description: 'La IP del dispositivo es requerida',
        variant: 'destructive'
      })
      return
    }

    setLoading(true)
    setCurrentStep('analyzing')
    setProgress({ message: 'Iniciando análisis completo...' })

    try {
      // Paso 1: Análisis completo
      setProgress({ message: 'Analizando dispositivo y obteniendo recomendaciones de IA...' })
      const analysis = await analyzer.analyzeStation(deviceIp, deviceMac || undefined)
      
      setAnalysisResult(analysis)
      saveToHistory(analysis)
      
      if (analysis.status === 'success') {
        toast({
          title: 'Análisis Completado',
          description: `Dispositivo identificado: ${analysis.identified_model}`
        })

        // Paso 2: Verificar si necesita habilitar frecuencias
        if (analysis.needs_frequency_enable) {
          setCurrentStep('frequency_prompt')
          setProgress({ 
            message: `La IA recomienda habilitar frecuencias para ${analysis.identified_model}`,
            recommendation: analysis.llm_analysis?.summary
          })
        } else {
          setCurrentStep('completed')
          setProgress({ message: 'Análisis completado exitosamente' })
        }
      } else {
        throw new Error(analysis.message || 'Error en análisis')
      }
    } catch (error) {
      console.error('Error en análisis:', error)
      toast({
        title: 'Error en Análisis',
        description: error.message,
        variant: 'destructive'
      })
      setCurrentStep('idle')
    } finally {
      setLoading(false)
    }
  }

  const handleEnableFrequencies = async () => {
    if (!analysisResult) return

    setLoading(true)
    setCurrentStep('enabling_frequencies')
    setProgress({ message: 'Habilitando frecuencias 5GHz...' })

    try {
      // Paso 3: Habilitar frecuencias
      const freqResult = await analyzer.enableFrequencies(
        analysisResult.ip, 
        analysisResult.identified_model
      )

      toast({
        title: 'Frecuencias Habilitadas',
        description: freqResult.message
      })

      // Paso 4: Esperar reconexión si el dispositivo se apagó
      if (freqResult.device_offline) {
        setCurrentStep('waiting_connection')
        setProgress({ 
          message: 'El dispositivo estará offline temporalmente. Esperando reconexión...',
          maxWait: 360
        })

        const connectionResult = await analyzer.waitForConnection(
          analysisResult.ip, 
          360
        )

        if (connectionResult.connection_restored) {
          toast({
            title: 'Dispositivo Reconectado',
            description: `Conexión restaurada después de ${connectionResult.attempts} intentos`
          })
          setCurrentStep('completed')
          setProgress({ 
            message: 'Análisis completado y dispositivo optimizado',
            connectionTime: connectionResult.elapsed_seconds
          })
        } else {
          throw new Error('El dispositivo no se reconectó en el tiempo esperado')
        }
      } else {
        setCurrentStep('completed')
        setProgress({ message: 'Frecuencias habilitadas exitosamente' })
      }
    } catch (error) {
      console.error('Error habilitando frecuencias:', error)
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive'
      })
      setCurrentStep('frequency_prompt')
    } finally {
      setLoading(false)
    }
  }

  const handleSkipFrequencies = () => {
    setCurrentStep('completed')
    setProgress({ message: 'Análisis completado (frecuencias no habilitadas)' })
  }

  const handleReset = () => {
    setDeviceIp('')
    setDeviceMac('')
    setAnalysisResult(null)
    setCurrentStep('idle')
    setProgress({})
    setFeedbackComment('')
    setFeedbackSubmitted(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Análisis de Estaciones</h1>
          <p className="text-gray-600">Análisis inteligente de dispositivos con IA y optimización automática</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="analyze">Análisis</TabsTrigger>
            <TabsTrigger value="history">Historial</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="feedback">Feedback</TabsTrigger>
          </TabsList>

          <TabsContent value="analyze" className="space-y-6">
            {/* Input Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Radio className="h-5 w-5" />
                  Configuración de Análisis
                </CardTitle>
                <CardDescription>
                  Ingresa la IP del dispositivo para iniciar el análisis completo
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="deviceIp">IP del Dispositivo *</Label>
                    <Input
                      id="deviceIp"
                      type="text"
                      placeholder="192.168.1.100"
                      value={deviceIp}
                      onChange={(e) => setDeviceIp(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="deviceMac">MAC (Opcional)</Label>
                    <Input
                      id="deviceMac"
                      type="text"
                      placeholder="00:27:22:XX:XX:XX"
                      value={deviceMac}
                      onChange={(e) => setDeviceMac(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    onClick={handleAnalyze} 
                    disabled={loading || !deviceIp}
                    className="flex items-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analizando...
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4" />
                        Iniciar Análisis
                      </>
                    )}
                  </Button>
                  
                  {currentStep !== 'idle' && (
                    <Button 
                      variant="outline" 
                      onClick={handleReset}
                      disabled={loading}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Nuevo Análisis
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Progress Section */}
            {currentStep !== 'idle' && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5" />
                    Progreso del Análisis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Step Indicator */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          ['analyzing', 'frequency_prompt', 'enabling_frequencies', 'waiting_connection', 'completed'].includes(currentStep) 
                            ? 'bg-green-500' 
                            : 'bg-gray-300'
                        }`} />
                        <span className="text-sm font-medium">Análisis</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          ['enabling_frequencies', 'waiting_connection', 'completed'].includes(currentStep) 
                            ? 'bg-green-500' 
                            : currentStep === 'frequency_prompt' ? 'bg-yellow-500' : 'bg-gray-300'
                        }`} />
                        <span className="text-sm font-medium">Frecuencias</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${
                          currentStep === 'completed' ? 'bg-green-500' : 'bg-gray-300'
                        }`} />
                        <span className="text-sm font-medium">Completado</span>
                      </div>
                    </div>

                    {/* Current Step Message */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                        <p className="text-sm text-blue-800">{progress.message}</p>
                      </div>
                      
                      {progress.recommendation && (
                        <div className="mt-2 p-2 bg-white rounded border">
                          <p className="text-xs font-medium text-gray-700 mb-1">Recomendación de IA:</p>
                          <p className="text-xs text-gray-600">{progress.recommendation}</p>
                        </div>
                      )}
                    </div>

                    {/* Frequency Prompt */}
                    {currentStep === 'frequency_prompt' && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                          <div className="flex-1">
                            <h4 className="font-medium text-yellow-800 mb-2">
                              ¿Habilitar frecuencias 5GHz?
                            </h4>
                            <p className="text-sm text-yellow-700 mb-3">
                              La IA recomienda habilitar frecuencias 5GHz para mejorar el rendimiento. 
                              Esto causará que el dispositivo se reinicie temporalmente.
                            </p>
                            <div className="flex gap-2">
                              <Button 
                                onClick={handleEnableFrequencies}
                                disabled={loading}
                                size="sm"
                                className="bg-green-600 hover:bg-green-700"
                              >
                                <Zap className="h-4 w-4 mr-2" />
                                Habilitar Frecuencias
                              </Button>
                              <Button 
                                variant="outline" 
                                onClick={handleSkipFrequencies}
                                disabled={loading}
                                size="sm"
                              >
                                Omitir por ahora
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Results Section */}
            {analysisResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    Resultados del Análisis
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Device Info */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm font-medium text-gray-600">IP</p>
                      <p className="text-lg font-semibold">{analysisResult.ip}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm font-medium text-gray-600">Modelo</p>
                      <p className="text-lg font-semibold uppercase">{analysisResult.identified_model}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm font-medium text-gray-600">Estado</p>
                      <p className="text-lg font-semibold capitalize">{analysisResult.status}</p>
                    </div>
                  </div>

                  {/* LLM Analysis */}
                  {analysisResult.llm_analysis && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 mb-3 flex items-center gap-2">
                        <MessageSquare className="h-4 w-4" />
                        Análisis de IA
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-blue-700 mb-1">Resumen:</p>
                          <p className="text-sm text-blue-600">{analysisResult.llm_analysis.summary}</p>
                        </div>
                        
                        {analysisResult.llm_analysis.recommendations && (
                          <div>
                            <p className="text-sm font-medium text-blue-700 mb-2">Recomendaciones:</p>
                            <ul className="space-y-1">
                              {analysisResult.llm_analysis.recommendations.map((rec, index) => (
                                <li key={index} className="text-sm text-blue-600 flex items-start gap-2">
                                  <span className="text-blue-400 mt-1">•</span>
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Device Data */}
                  {analysisResult.device_data && (
                    <div>
                      <h4 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
                        <Server className="h-4 w-4" />
                        Datos del Dispositivo
                      </h4>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <pre className="text-xs text-gray-600 overflow-x-auto">
                          {JSON.stringify(analysisResult.device_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Feedback Section */}
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-800 mb-3">Feedback del Análisis</h4>
                    {!feedbackSubmitted ? (
                      <div className="space-y-3">
                        <Textarea
                          placeholder="¿Fue útil este análisis? ¿Hay algo que podamos mejorar?"
                          value={feedbackComment}
                          onChange={(e) => setFeedbackComment(e.target.value)}
                          rows={3}
                        />
                        <div className="flex gap-2">
                          <Button 
                            onClick={handleFeedback}
                            disabled={!feedbackComment.trim()}
                            size="sm"
                          >
                            <ThumbsUp className="h-4 w-4 mr-2" />
                            Enviar Feedback
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <p className="text-sm text-green-800">✅ Gracias por tu feedback</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Historial de Análisis
                </CardTitle>
              </CardHeader>
              <CardContent>
                {history.length > 0 ? (
                  <div className="space-y-3">
                    {history.map((item) => (
                      <div key={item.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <span className="font-medium">{item.ip}</span>
                            <span className="text-sm text-gray-500 uppercase">{item.model}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              item.status === 'success' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {item.status}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(item.timestamp).toLocaleString()}
                          </span>
                        </div>
                        {item.llm_analysis?.summary && (
                          <p className="text-sm text-gray-600">{item.llm_analysis.summary}</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <History className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>No hay análisis anteriores</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Logs del Sistema
                </CardTitle>
                <CardDescription>
                  Visualiza y busca logs de las operaciones del sistema
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Search and Filters */}
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1">
                    <Input
                      placeholder="Buscar en logs..."
                      value={logsSearchQuery}
                      onChange={(e) => setLogsSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && searchLogs()}
                    />
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={logsFilters.level}
                      onChange={(e) => setLogsFilters({...logsFilters, level: e.target.value})}
                      className="px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="">Todos los niveles</option>
                      <option value="ERROR">Error</option>
                      <option value="WARNING">Warning</option>
                      <option value="INFO">Info</option>
                      <option value="DEBUG">Debug</option>
                    </select>
                    <Button onClick={searchLogs} disabled={logsLoading}>
                      {logsLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Search className="h-4 w-4" />
                      )}
                    </Button>
                    <Button onClick={fetchRecentLogs} variant="outline" disabled={logsLoading}>
                      <Clock className="h-4 w-4 mr-2" />
                      Recientes
                    </Button>
                    <Button onClick={clearLogs} variant="destructive" disabled={logsLoading}>
                      <XCircle className="h-4 w-4 mr-2" />
                      Limpiar
                    </Button>
                  </div>
                </div>

                {/* Logs Display */}
                <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
                  {logsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                    </div>
                  ) : logs.length > 0 ? (
                    <div className="space-y-1">
                      {logs.map((log, index) => (
                        <div key={index} className="font-mono text-xs text-gray-300">
                          <span className="text-gray-500">
                            {log.timestamp || new Date().toISOString()}
                          </span>
                          <span className={`ml-2 ${
                            log.level === 'ERROR' ? 'text-red-400' :
                            log.level === 'WARNING' ? 'text-yellow-400' :
                            log.level === 'INFO' ? 'text-blue-400' :
                            'text-gray-400'
                          }`}>
                            [{log.level || 'INFO'}]
                          </span>
                          <span className="ml-2">{log.message || log}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <FileText className="h-12 w-12 mx-auto mb-2 text-gray-600" />
                      <p>No hay logs para mostrar</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="feedback" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Feedback de Usuarios
                </CardTitle>
                <CardDescription>
                  Lista de todos los feedbacks enviados por los usuarios
                </CardDescription>
              </CardHeader>
              <CardContent>
                {feedbackLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : feedbackList.length > 0 ? (
                  <div className="space-y-4">
                    {feedbackList.map((feedback, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <span className="font-medium">Análisis #{feedback.analysis_id}</span>
                            <div className="flex items-center gap-1">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  className={`h-4 w-4 ${
                                    i < (feedback.rating || 5) 
                                      ? 'text-yellow-400 fill-current' 
                                      : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(feedback.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{feedback.comment}</p>
                        {feedback.user_agent && (
                          <p className="text-xs text-gray-400 mt-2">
                            {feedback.user_agent}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>No hay feedbacks registrados</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
