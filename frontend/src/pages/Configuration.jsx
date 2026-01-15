import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Save, Settings } from 'lucide-react'

export default function Configuration() {
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingConfig, setEditingConfig] = useState({})
  const { toast } = useToast()

  const fetchConfigs = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getSystemConfig()
      setConfigs(response.data.configs)
      
      const editing = {}
      response.data.configs.forEach(config => {
        editing[config.key] = config.value
      })
      setEditingConfig(editing)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar configuraciones',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  const handleSaveConfig = async (key, valueType) => {
    try {
      await adminApi.updateConfig(key, {
        value: editingConfig[key],
        value_type: valueType,
        updated_by: 'admin',
        performed_by: 'admin'
      })
      toast({
        title: 'Configuración Actualizada',
        description: `${key} ha sido actualizado exitosamente`
      })
      fetchConfigs()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar configuración',
        variant: 'destructive'
      })
    }
  }

  const handleInputChange = (key, value) => {
    setEditingConfig(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const groupByCategory = (configs) => {
    const grouped = {}
    configs.forEach(config => {
      const category = config.category || 'general'
      if (!grouped[category]) {
        grouped[category] = []
      }
      grouped[category].push(config)
    })
    return grouped
  }

  const getCategoryTitle = (category) => {
    const titles = {
      'notifications': 'Notificaciones',
      'schedules': 'Horarios',
      'thresholds': 'Umbrales',
      'system': 'Sistema',
      'general': 'General'
    }
    return titles[category] || category
  }

  const getCategoryDescription = (category) => {
    const descriptions = {
      'notifications': 'Configuración de alertas y notificaciones por WhatsApp',
      'schedules': 'Configuración de horarios de trabajo',
      'thresholds': 'Umbrales de tiempo para alertas',
      'system': 'Configuración general del sistema',
      'general': 'Configuraciones generales'
    }
    return descriptions[category] || ''
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const groupedConfigs = groupByCategory(configs)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Configuración del Sistema</h1>
          <p className="text-muted-foreground">
            Administra parámetros globales del sistema
          </p>
        </div>
        <Button onClick={fetchConfigs} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Configuration Categories */}
      {Object.entries(groupedConfigs).map(([category, categoryConfigs]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              {getCategoryTitle(category)}
            </CardTitle>
            <CardDescription>
              {getCategoryDescription(category)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {categoryConfigs.map((config) => (
                <div key={config.key} className="flex items-center gap-4 p-4 border rounded-lg">
                  <div className="flex-1 space-y-1">
                    <div className="font-medium text-sm">{config.key}</div>
                    <div className="text-xs text-muted-foreground">
                      {config.description || 'Sin descripción'}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {config.value_type === 'bool' ? (
                      <select
                        value={editingConfig[config.key] || config.value}
                        onChange={(e) => handleInputChange(config.key, e.target.value)}
                        className="px-3 py-2 border rounded-md text-sm"
                      >
                        <option value="true">Activado</option>
                        <option value="false">Desactivado</option>
                      </select>
                    ) : config.value_type === 'int' ? (
                      <input
                        type="number"
                        value={editingConfig[config.key] || config.value}
                        onChange={(e) => handleInputChange(config.key, e.target.value)}
                        className="px-3 py-2 border rounded-md text-sm w-32"
                      />
                    ) : (
                      <input
                        type="text"
                        value={editingConfig[config.key] || config.value}
                        onChange={(e) => handleInputChange(config.key, e.target.value)}
                        className="px-3 py-2 border rounded-md text-sm w-48"
                      />
                    )}
                    <Button
                      onClick={() => handleSaveConfig(config.key, config.value_type)}
                      size="sm"
                      disabled={editingConfig[config.key] === config.value}
                    >
                      <Save className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Información Importante</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>• Los cambios en la configuración se aplican inmediatamente</p>
          <p>• Los valores booleanos controlan activación/desactivación de funcionalidades</p>
          <p>• Los valores numéricos representan minutos o IDs según el contexto</p>
          <p>• Todos los cambios quedan registrados en el log de auditoría</p>
        </CardContent>
      </Card>
    </div>
  )
}
