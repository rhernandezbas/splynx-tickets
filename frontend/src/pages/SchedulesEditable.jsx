import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Clock, Plus, Edit, Trash2, Save, X } from 'lucide-react'

export default function SchedulesEditable() {
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
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

  const handleAddSchedule = (personId, scheduleType = 'work') => {
    setNewSchedule({
      person_id: personId,
      day_of_week: 0,
      start_time: '09:00',
      end_time: '17:00',
      schedule_type: scheduleType,
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
        description: 'El horario ha sido creado exitosamente'
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
        day_of_week: editingSchedule.day_of_week,
        start_time: editingSchedule.start_time,
        end_time: editingSchedule.end_time,
        is_active: editingSchedule.is_active,
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

  const groupSchedulesByDay = (schedules) => {
    const grouped = {}
    schedules.forEach(schedule => {
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
            Administra los horarios de trabajo de cada operador
          </p>
        </div>
        <Button onClick={fetchOperators} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Schedules Grid */}
      <div className="grid gap-6">
        {operators.map((operator) => {
          const groupedSchedules = groupSchedulesByDay(operator.schedules || [])
          const isAddingSchedule = newSchedule?.person_id === operator.person_id
          
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
                      {operator.schedules?.length || 0} horarios configurados
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
                  <div className="mb-4 p-4 border-2 border-green-200 rounded-lg bg-green-50">
                    <h4 className="font-medium mb-3 text-green-900">Nuevo Horario</h4>
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
                          <Save className="h-4 w-4 mr-2" />
                          Guardar
                        </Button>
                        <Button onClick={() => setNewSchedule(null)} variant="outline" size="sm">
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Schedules List */}
                {operator.schedules && operator.schedules.length > 0 ? (
                  <div className="space-y-3">
                    {[0, 1, 2, 3, 4, 5, 6].map((day) => {
                      const daySchedules = groupedSchedules[day] || []
                      return (
                        <div key={day} className="flex items-start justify-between py-2 border-b last:border-0">
                          <div className="font-medium text-sm w-32 pt-2">
                            {getDayName(day)}
                          </div>
                          <div className="flex-1">
                            {daySchedules.length > 0 ? (
                              <div className="space-y-2">
                                {daySchedules.map((schedule) => (
                                  <div key={schedule.id}>
                                    {editingSchedule?.id === schedule.id ? (
                                      <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-md">
                                        <select
                                          value={editingSchedule.day_of_week}
                                          onChange={(e) => setEditingSchedule({ ...editingSchedule, day_of_week: parseInt(e.target.value) })}
                                          className="px-2 py-1 border rounded text-sm"
                                        >
                                          {daysOfWeek.map(d => (
                                            <option key={d.value} value={d.value}>{d.label}</option>
                                          ))}
                                        </select>
                                        <input
                                          type="time"
                                          value={editingSchedule.start_time}
                                          onChange={(e) => setEditingSchedule({ ...editingSchedule, start_time: e.target.value })}
                                          className="px-2 py-1 border rounded text-sm w-28"
                                        />
                                        <span>-</span>
                                        <input
                                          type="time"
                                          value={editingSchedule.end_time}
                                          onChange={(e) => setEditingSchedule({ ...editingSchedule, end_time: e.target.value })}
                                          className="px-2 py-1 border rounded text-sm w-28"
                                        />
                                        <label className="flex items-center gap-1 text-sm">
                                          <input
                                            type="checkbox"
                                            checked={editingSchedule.is_active}
                                            onChange={(e) => setEditingSchedule({ ...editingSchedule, is_active: e.target.checked })}
                                          />
                                          Activo
                                        </label>
                                        <Button onClick={handleSaveSchedule} size="sm" variant="default">
                                          <Save className="h-3 w-3" />
                                        </Button>
                                        <Button onClick={() => setEditingSchedule(null)} size="sm" variant="outline">
                                          <X className="h-3 w-3" />
                                        </Button>
                                      </div>
                                    ) : (
                                      <div className="flex items-center gap-2">
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                          schedule.is_active ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                                        }`}>
                                          {schedule.start_time} - {schedule.end_time}
                                        </span>
                                        <Button
                                          onClick={() => handleEditSchedule(schedule)}
                                          size="sm"
                                          variant="ghost"
                                          className="h-7 w-7 p-0"
                                        >
                                          <Edit className="h-3 w-3" />
                                        </Button>
                                        <Button
                                          onClick={() => handleDeleteSchedule(schedule.id)}
                                          size="sm"
                                          variant="ghost"
                                          className="h-7 w-7 p-0 text-red-600 hover:text-red-700"
                                        >
                                          <Trash2 className="h-3 w-3" />
                                        </Button>
                                      </div>
                                    )}
                                  </div>
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
                  <div className="text-center py-8 text-muted-foreground">
                    No hay horarios configurados para este operador
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Información sobre Horarios</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>• Los horarios se configuran por día de la semana (Lunes a Domingo)</p>
          <p>• Formato de hora: HH:MM (24 horas)</p>
          <p>• Los operadores solo reciben asignaciones durante sus horarios activos</p>
          <p>• Puedes agregar múltiples horarios para el mismo día</p>
          <p>• Fin de semana: Solo el operador de guardia trabaja (9:00-21:00)</p>
          <p>• Todos los cambios quedan registrados en el log de auditoría</p>
        </CardContent>
      </Card>
    </div>
  )
}
