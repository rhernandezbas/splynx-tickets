import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Clock, Plus, Edit, Trash2, Save, X, Briefcase, Bell } from 'lucide-react'

export default function SchedulesDual() {
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('work') // 'work' o 'alert'
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [newSchedule, setNewSchedule] = useState(null)
  const { toast } = useToast()

  const daysOfWeek = [
    { value: 0, label: 'Lunes' },
    { value: 1, label: 'Martes' },
    { value: 2, label: 'Miércoles' },
    { value: 3, label: 'Jueves' },
    { value: 4, label: 'Viernes' },
    { value: 5, label: 'Sábado' },
    { value: 6, label: 'Domingo' }
  ]

  const fetchOperators = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getOperators()
      setOperators(response.data.operators)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar horarios',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOperators()
  }, [])

  const handleAddSchedule = (personId) => {
    setNewSchedule({
      person_id: personId,
      day_of_week: 0,
      start_time: activeTab === 'work' ? '08:00' : '10:00',
      end_time: activeTab === 'work' ? '17:00' : '18:00',
      schedule_type: activeTab,
      is_active: true
    })
  }

  const handleSaveNewSchedule = async () => {
    try {
      await adminApi.createSchedule({
        ...newSchedule,
        performed_by: 'admin'
      })
      toast({
        title: 'Horario Creado',
        description: `Horario de ${activeTab === 'work' ? 'trabajo' : 'alertas'} creado exitosamente`
      })
      setNewSchedule(null)
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al crear horario',
        variant: 'destructive'
      })
    }
  }

  const handleEditSchedule = (schedule) => {
    setEditingSchedule({ ...schedule })
  }

  const handleSaveSchedule = async () => {
    try {
      await adminApi.updateSchedule(editingSchedule.id, {
        ...editingSchedule,
        performed_by: 'admin'
      })
      toast({
        title: 'Horario Actualizado',
        description: 'El horario ha sido actualizado exitosamente'
      })
      setEditingSchedule(null)
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar horario',
        variant: 'destructive'
      })
    }
  }

  const handleDeleteSchedule = async (scheduleId) => {
    if (!confirm('¿Estás seguro de eliminar este horario?')) return
    
    try {
      await adminApi.deleteSchedule(scheduleId)
      toast({
        title: 'Horario Eliminado',
        description: 'El horario ha sido eliminado exitosamente'
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al eliminar horario',
        variant: 'destructive'
      })
    }
  }

  const getDayName = (day) => {
    return daysOfWeek.find(d => d.value === day)?.label || 'Desconocido'
  }

  const filterSchedulesByType = (schedules) => {
    return schedules.filter(s => (s.schedule_type || 'alert') === activeTab)
  }

  const groupSchedulesByDay = (schedules) => {
    const filtered = filterSchedulesByType(schedules)
    const grouped = {}
    filtered.forEach(schedule => {
      if (!grouped[schedule.day_of_week]) {
        grouped[schedule.day_of_week] = []
      }
      grouped[schedule.day_of_week].push(schedule)
    })
    return grouped
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
          <h1 className="text-3xl font-bold tracking-tight">Gestión de Horarios</h1>
          <p className="text-muted-foreground">
            Administra los horarios de trabajo y alertas de cada operador
          </p>
        </div>
        <Button onClick={fetchOperators} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('work')}
          className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'work'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Briefcase className="h-4 w-4" />
          Horarios de Trabajo
        </button>
        <button
          onClick={() => setActiveTab('alert')}
          className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'alert'
              ? 'border-b-2 border-orange-600 text-orange-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Bell className="h-4 w-4" />
          Horarios de Alertas
        </button>
      </div>

      {/* Info Card */}
      <Card className={activeTab === 'work' ? 'bg-blue-50 border-blue-200' : 'bg-orange-50 border-orange-200'}>
        <CardContent className="pt-6">
          <p className={`text-sm ${activeTab === 'work' ? 'text-blue-800' : 'text-orange-800'}`}>
            {activeTab === 'work' ? (
              <>
                <strong>Horarios de Trabajo:</strong> Define los horarios laborales de cada operador. 
                Durante estos horarios, el operador estará disponible para recibir asignaciones de tickets.
              </>
            ) : (
              <>
                <strong>Horarios de Alertas:</strong> Define los horarios en los que el operador recibirá 
                notificaciones de WhatsApp sobre tickets vencidos o que requieren atención urgente.
              </>
            )}
          </p>
        </CardContent>
      </Card>

      {/* Schedules Grid */}
      <div className="grid gap-6">
        {operators.map((operator) => {
          const groupedSchedules = groupSchedulesByDay(operator.schedules || [])
          const isAddingSchedule = newSchedule?.person_id === operator.person_id
          const scheduleCount = filterSchedulesByType(operator.schedules || []).length
          
          return (
            <Card key={operator.person_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5" />
                      {operator.name}
                    </CardTitle>
                    <CardDescription>
                      {scheduleCount} horario{scheduleCount !== 1 ? 's' : ''} de {activeTab === 'work' ? 'trabajo' : 'alertas'} configurado{scheduleCount !== 1 ? 's' : ''}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right mr-4">
                      <div className="text-sm font-medium">
                        {operator.is_paused ? (
                          <span className="text-orange-600">Pausado</span>
                        ) : operator.is_active ? (
                          <span className="text-green-600">Activo</span>
                        ) : (
                          <span className="text-gray-600">Inactivo</span>
                        )}
                      </div>
                    </div>
                    <Button
                      onClick={() => handleAddSchedule(operator.person_id)}
                      size="sm"
                      disabled={isAddingSchedule}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Agregar Horario
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* New Schedule Form */}
                {isAddingSchedule && (
                  <div className={`mb-4 p-4 border-2 rounded-lg ${
                    activeTab === 'work' ? 'border-blue-200 bg-blue-50' : 'border-orange-200 bg-orange-50'
                  }`}>
                    <h4 className={`font-medium mb-3 ${activeTab === 'work' ? 'text-blue-900' : 'text-orange-900'}`}>
                      Nuevo Horario de {activeTab === 'work' ? 'Trabajo' : 'Alertas'}
                    </h4>
                    <div className="grid grid-cols-4 gap-3">
                      <div>
                        <label className="text-sm font-medium block mb-1">Día</label>
                        <select
                          value={newSchedule.day_of_week}
                          onChange={(e) => setNewSchedule({ ...newSchedule, day_of_week: parseInt(e.target.value) })}
                          className="w-full px-3 py-2 border rounded-md text-sm"
                        >
                          {daysOfWeek.map(day => (
                            <option key={day.value} value={day.value}>{day.label}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-sm font-medium block mb-1">Hora Inicio</label>
                        <input
                          type="time"
                          value={newSchedule.start_time}
                          onChange={(e) => setNewSchedule({ ...newSchedule, start_time: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium block mb-1">Hora Fin</label>
                        <input
                          type="time"
                          value={newSchedule.end_time}
                          onChange={(e) => setNewSchedule({ ...newSchedule, end_time: e.target.value })}
                          className="w-full px-3 py-2 border rounded-md text-sm"
                        />
                      </div>
                      <div className="flex items-end gap-2">
                        <Button onClick={handleSaveNewSchedule} size="sm" className="flex-1">
                          <Save className="h-4 w-4 mr-1" />
                          Guardar
                        </Button>
                        <Button onClick={() => setNewSchedule(null)} size="sm" variant="outline">
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Schedules Table */}
                <div className="space-y-2">
                  {daysOfWeek.map(day => {
                    const daySchedules = groupedSchedules[day.value] || []
                    if (daySchedules.length === 0) return null
                    
                    return (
                      <div key={day.value} className="border rounded-lg p-3">
                        <div className="font-medium text-sm mb-2">{day.label}</div>
                        <div className="space-y-2">
                          {daySchedules.map(schedule => {
                            const isEditing = editingSchedule?.id === schedule.id
                            
                            return (
                              <div key={schedule.id} className="flex items-center gap-2 bg-gray-50 p-2 rounded">
                                {isEditing ? (
                                  <>
                                    <input
                                      type="time"
                                      value={editingSchedule.start_time}
                                      onChange={(e) => setEditingSchedule({ ...editingSchedule, start_time: e.target.value })}
                                      className="px-2 py-1 border rounded text-sm"
                                    />
                                    <span>-</span>
                                    <input
                                      type="time"
                                      value={editingSchedule.end_time}
                                      onChange={(e) => setEditingSchedule({ ...editingSchedule, end_time: e.target.value })}
                                      className="px-2 py-1 border rounded text-sm"
                                    />
                                    <Button onClick={handleSaveSchedule} size="sm" variant="outline">
                                      <Save className="h-3 w-3" />
                                    </Button>
                                    <Button onClick={() => setEditingSchedule(null)} size="sm" variant="outline">
                                      <X className="h-3 w-3" />
                                    </Button>
                                  </>
                                ) : (
                                  <>
                                    <span className="text-sm font-mono bg-white px-3 py-1 rounded border">
                                      {schedule.start_time} - {schedule.end_time}
                                    </span>
                                    <div className="flex-1"></div>
                                    <Button onClick={() => handleEditSchedule(schedule)} size="sm" variant="outline">
                                      <Edit className="h-3 w-3" />
                                    </Button>
                                    <Button onClick={() => handleDeleteSchedule(schedule.id)} size="sm" variant="outline" className="text-red-600 hover:text-red-700">
                                      <Trash2 className="h-3 w-3" />
                                    </Button>
                                  </>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                  {Object.keys(groupedSchedules).length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      No hay horarios de {activeTab === 'work' ? 'trabajo' : 'alertas'} configurados
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
