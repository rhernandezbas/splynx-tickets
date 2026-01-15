import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { 
  RefreshCw, UserPlus, Edit2, Trash2, Clock, Bell, BellOff, 
  Phone, Pause, Play, UserCheck, UserX, Plus, Save, X, Briefcase
} from 'lucide-react'

export default function OperatorsManagement() {
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingOperator, setEditingOperator] = useState(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  const [activeScheduleTab, setActiveScheduleTab] = useState('work')
  const [newSchedule, setNewSchedule] = useState(null)
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [configForm, setConfigForm] = useState({
    is_paused: false,
    assignment_paused: false,
    notifications_enabled: true,
    whatsapp_number: '',
    paused_reason: ''
  })
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
      setOperators(response.data.operators || [])
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar operadores',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOperators()
  }, [])

  const handleOpenConfig = (operator) => {
    setEditingOperator(operator)
    setConfigForm({
      is_paused: operator.is_paused || false,
      assignment_paused: operator.assignment_paused || false,
      notifications_enabled: operator.notifications_enabled !== false,
      whatsapp_number: operator.whatsapp_number || '',
      paused_reason: operator.paused_reason || ''
    })
    setConfigDialogOpen(true)
  }

  const handleSaveConfig = async () => {
    try {
      await adminApi.updateOperatorConfig(editingOperator.person_id, {
        ...configForm,
        paused_by: 'admin'
      })
      toast({
        title: 'Configuración Actualizada',
        description: `Configuración de ${editingOperator.name} actualizada exitosamente`
      })
      setConfigDialogOpen(false)
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar configuración',
        variant: 'destructive'
      })
    }
  }

  const handlePauseOperator = async (personId, name) => {
    const reason = prompt(`¿Por qué deseas pausar a ${name}?`)
    if (!reason) return

    try {
      await adminApi.pauseOperator(personId, {
        reason,
        paused_by: 'admin',
        performed_by: 'admin'
      })
      toast({
        title: 'Operador Pausado',
        description: `${name} ha sido pausado exitosamente`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al pausar operador',
        variant: 'destructive'
      })
    }
  }

  const handleResumeOperator = async (personId, name) => {
    try {
      await adminApi.resumeOperator(personId)
      toast({
        title: 'Operador Reanudado',
        description: `${name} ha sido reanudado exitosamente`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al reanudar operador',
        variant: 'destructive'
      })
    }
  }

  const handleToggleNotifications = async (personId, name, currentState) => {
    try {
      await adminApi.updateOperator(personId, {
        notifications_enabled: !currentState,
        performed_by: 'admin'
      })
      toast({
        title: 'Notificaciones Actualizadas',
        description: `Notificaciones ${!currentState ? 'activadas' : 'desactivadas'} para ${name}`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar notificaciones',
        variant: 'destructive'
      })
    }
  }

  const handleToggleActive = async (personId, name, currentState) => {
    if (!confirm(`¿Estás seguro de ${currentState ? 'desactivar' : 'activar'} a ${name}?`)) return

    try {
      await adminApi.updateOperator(personId, {
        is_active: !currentState,
        performed_by: 'admin'
      })
      toast({
        title: 'Estado Actualizado',
        description: `${name} ha sido ${!currentState ? 'activado' : 'desactivado'}`
      })
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar estado',
        variant: 'destructive'
      })
    }
  }

  const handleSaveOperator = async () => {
    try {
      await adminApi.updateOperator(editingOperator.person_id, {
        whatsapp_number: editingOperator.whatsapp_number,
        performed_by: 'admin'
      })
      toast({
        title: 'Operador Actualizado',
        description: 'Teléfono actualizado exitosamente'
      })
      setEditDialogOpen(false)
      setEditingOperator(null)
      fetchOperators()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al actualizar operador',
        variant: 'destructive'
      })
    }
  }

  const handleAddSchedule = (personId) => {
    const defaultTimes = {
      work: { start: '08:00', end: '17:00' },
      assignment: { start: '08:00', end: '16:00' },
      alert: { start: '08:00', end: '17:00' }
    }
    const times = defaultTimes[activeScheduleTab] || defaultTimes.work
    
    setNewSchedule({
      person_id: personId,
      day_of_week: 0,
      start_time: times.start,
      end_time: times.end,
      schedule_type: activeScheduleTab,
      is_active: true
    })
  }

  const handleSaveNewSchedule = async () => {
    try {
      await adminApi.createSchedule({
        ...newSchedule,
        schedule_type: activeScheduleTab,
        performed_by: 'admin'
      })
      const typeNames = {
        work: 'trabajo',
        assignment: 'asignación',
        alert: 'alertas'
      }
      toast({
        title: 'Horario Creado',
        description: `Horario de ${typeNames[activeScheduleTab]} creado exitosamente`
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
    return schedules.filter(s => s.schedule_type === activeScheduleTab)
  }

  const groupSchedulesByDay = (schedules) => {
    const filtered = filterSchedulesByType(schedules)
    return filtered.reduce((acc, schedule) => {
      if (!acc[schedule.day_of_week]) {
        acc[schedule.day_of_week] = []
      }
      acc[schedule.day_of_week].push(schedule)
      return acc
    }, {})
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
          <h1 className="text-3xl font-bold tracking-tight">Gestión de Operadores</h1>
          <p className="text-muted-foreground">
            Administra operadores, horarios de asignación y alertas
          </p>
        </div>
        <Button onClick={fetchOperators} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="operators" className="space-y-4">
        <TabsList>
          <TabsTrigger value="operators">
            <UserCheck className="h-4 w-4 mr-2" />
            Operadores
          </TabsTrigger>
          <TabsTrigger value="schedules">
            <Clock className="h-4 w-4 mr-2" />
            Horarios
          </TabsTrigger>
        </TabsList>

        {/* Operators Tab */}
        <TabsContent value="operators" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
            {operators.map((operator) => (
              <Card key={operator.person_id} className={operator.is_paused ? 'border-orange-300' : ''}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="flex items-center gap-2 flex-wrap">
                        {operator.name}
                        {operator.is_paused && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                            🔴 Pausado Total
                          </span>
                        )}
                        {!operator.is_paused && operator.assignment_paused && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            🚫 Sin Asignación
                          </span>
                        )}
                        {!operator.notifications_enabled && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            🔕 Sin Notif.
                          </span>
                        )}
                        {!operator.is_active && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            ❌ Inactivo
                          </span>
                        )}
                      </CardTitle>
                      <CardDescription>
                        ID: {operator.person_id} • WhatsApp: {operator.whatsapp_number || 'No configurado'}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-primary">{operator.ticket_count}</div>
                      <div className="text-xs text-muted-foreground">Asignados</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">
                        {operator.schedules?.filter(s => s.schedule_type === 'work').length || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">Horarios</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-orange-600">
                        {operator.notifications_enabled ? (
                          <Bell className="h-6 w-6 mx-auto" />
                        ) : (
                          <BellOff className="h-6 w-6 mx-auto" />
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground">Notif.</div>
                    </div>
                  </div>

                  {/* Pause Reason */}
                  {operator.is_paused && operator.paused_reason && (
                    <div className="p-3 bg-orange-50 border border-orange-200 rounded-md">
                      <p className="text-sm text-orange-800">
                        <strong>Razón:</strong> {operator.paused_reason}
                      </p>
                      {operator.paused_at && (
                        <p className="text-xs text-orange-600 mt-1">
                          Pausado: {new Date(operator.paused_at).toLocaleString('es-AR')}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex flex-wrap gap-2 pt-2 border-t">
                    <Button
                      onClick={() => handleOpenConfig(operator)}
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      title="Configuración completa"
                    >
                      <Briefcase className="h-4 w-4 mr-2" />
                      Configurar
                    </Button>

                    {operator.is_paused ? (
                      <Button
                        onClick={() => handleResumeOperator(operator.person_id, operator.name)}
                        size="sm"
                        variant="default"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        onClick={() => handlePauseOperator(operator.person_id, operator.name)}
                        size="sm"
                        variant="outline"
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    )}

                    <Button
                      onClick={() => {
                        setEditingOperator(operator)
                        setEditDialogOpen(true)
                      }}
                      size="sm"
                      variant="outline"
                      title="Editar horarios"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>

                    <Button
                      onClick={() => handleToggleActive(operator.person_id, operator.name, operator.is_active)}
                      size="sm"
                      variant={operator.is_active ? "destructive" : "default"}
                      title={operator.is_active ? 'Desactivar' : 'Activar'}
                    >
                      {operator.is_active ? (
                        <UserX className="h-4 w-4" />
                      ) : (
                        <UserCheck className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Resumen</CardTitle>
              <CardDescription>Estado general de operadores</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold">{operators.length}</div>
                  <div className="text-sm text-muted-foreground">Total</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {operators.filter(o => o.is_active && !o.is_paused).length}
                  </div>
                  <div className="text-sm text-muted-foreground">Activos</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">
                    {operators.filter(o => o.is_paused).length}
                  </div>
                  <div className="text-sm text-muted-foreground">Pausados</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-600">
                    {operators.filter(o => !o.is_active).length}
                  </div>
                  <div className="text-sm text-muted-foreground">Inactivos</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedules Tab */}
        <TabsContent value="schedules" className="space-y-4">
          {/* Schedule Type Tabs */}
          <div className="flex gap-2 border-b">
            <button
              onClick={() => setActiveScheduleTab('work')}
              className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
                activeScheduleTab === 'work'
                  ? 'border-b-2 border-green-600 text-green-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Clock className="h-4 w-4" />
              Horarios de Trabajo
            </button>
            <button
              onClick={() => setActiveScheduleTab('assignment')}
              className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
                activeScheduleTab === 'assignment'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Briefcase className="h-4 w-4" />
              Horarios de Asignación
            </button>
            <button
              onClick={() => setActiveScheduleTab('alert')}
              className={`px-4 py-2 font-medium transition-colors flex items-center gap-2 ${
                activeScheduleTab === 'alert'
                  ? 'border-b-2 border-orange-600 text-orange-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Bell className="h-4 w-4" />
              Horarios de Alertas
            </button>
          </div>

          {/* Info Card */}
          <Card className={
            activeScheduleTab === 'work' ? 'bg-green-50 border-green-200' :
            activeScheduleTab === 'assignment' ? 'bg-blue-50 border-blue-200' : 
            'bg-orange-50 border-orange-200'
          }>
            <CardContent className="pt-6">
              <p className={`text-sm ${
                activeScheduleTab === 'work' ? 'text-green-800' :
                activeScheduleTab === 'assignment' ? 'text-blue-800' : 
                'text-orange-800'
              }`}>
                {activeScheduleTab === 'work' ? (
                  <>
                    <strong>Horarios de Trabajo:</strong> Define el horario laboral general del operador. 
                    Este es el horario en el que el operador está disponible para trabajar.
                  </>
                ) : activeScheduleTab === 'assignment' ? (
                  <>
                    <strong>Horarios de Asignación:</strong> Define los horarios en los que el operador puede recibir asignaciones de tickets. 
                    Durante estos horarios, el sistema asignará automáticamente tickets nuevos al operador.
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
                          {scheduleCount} horario{scheduleCount !== 1 ? 's' : ''} de {
                            activeScheduleTab === 'work' ? 'trabajo' :
                            activeScheduleTab === 'assignment' ? 'asignación' : 
                            'alertas'
                          } configurado{scheduleCount !== 1 ? 's' : ''}
                        </CardDescription>
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
                  </CardHeader>
                  <CardContent>
                    {/* New Schedule Form */}
                    {isAddingSchedule && (
                      <div className={`mb-4 p-4 border-2 rounded-lg ${
                        activeScheduleTab === 'work' ? 'border-green-200 bg-green-50' :
                        activeScheduleTab === 'assignment' ? 'border-blue-200 bg-blue-50' : 
                        'border-orange-200 bg-orange-50'
                      }`}>
                        <h4 className={`font-medium mb-3 ${
                          activeScheduleTab === 'work' ? 'text-green-900' :
                          activeScheduleTab === 'assignment' ? 'text-blue-900' : 
                          'text-orange-900'
                        }`}>
                          Nuevo Horario de {
                            activeScheduleTab === 'work' ? 'Trabajo' :
                            activeScheduleTab === 'assignment' ? 'Asignación' : 
                            'Alertas'
                          }
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
                            <label className="text-sm font-medium block mb-1">Inicio</label>
                            <input
                              type="time"
                              value={newSchedule.start_time}
                              onChange={(e) => setNewSchedule({ ...newSchedule, start_time: e.target.value })}
                              className="w-full px-3 py-2 border rounded-md text-sm"
                            />
                          </div>
                          <div>
                            <label className="text-sm font-medium block mb-1">Fin</label>
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

                    {/* Schedules by Day */}
                    <div className="space-y-3">
                      {daysOfWeek.map(day => {
                        const daySchedules = groupedSchedules[day.value] || []
                        if (daySchedules.length === 0) return null

                        return (
                          <div key={day.value} className="border-b pb-3 last:border-0">
                            <h4 className="font-medium text-sm mb-2">{day.label}</h4>
                            <div className="space-y-2">
                              {daySchedules.map(schedule => (
                                <div key={schedule.id} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                                  {editingSchedule?.id === schedule.id ? (
                                    <div className="flex items-center gap-2 flex-1">
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
                                      <Button onClick={handleSaveSchedule} size="sm" variant="default">
                                        <Save className="h-3 w-3" />
                                      </Button>
                                      <Button onClick={() => setEditingSchedule(null)} size="sm" variant="outline">
                                        <X className="h-3 w-3" />
                                      </Button>
                                    </div>
                                  ) : (
                                    <>
                                      <span className="text-sm">
                                        {schedule.start_time} - {schedule.end_time}
                                      </span>
                                      <div className="flex gap-1">
                                        <Button
                                          onClick={() => handleEditSchedule(schedule)}
                                          size="sm"
                                          variant="ghost"
                                        >
                                          <Edit2 className="h-3 w-3" />
                                        </Button>
                                        <Button
                                          onClick={() => handleDeleteSchedule(schedule.id)}
                                          size="sm"
                                          variant="ghost"
                                        >
                                          <Trash2 className="h-3 w-3" />
                                        </Button>
                                      </div>
                                    </>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                      {Object.keys(groupedSchedules).length === 0 && (
                        <div className="text-center py-8 text-gray-500">
                          No hay horarios de {
                            activeScheduleTab === 'work' ? 'trabajo' :
                            activeScheduleTab === 'assignment' ? 'asignación' : 
                            'alertas'
                          } configurados
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>
      </Tabs>

      {/* Config Operator Dialog - Pausas Granulares */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Configuración de {editingOperator?.name}</DialogTitle>
            <DialogDescription>
              Gestiona pausas y configuración del operador
            </DialogDescription>
          </DialogHeader>
          {editingOperator && (
            <div className="space-y-4">
              {/* Número de WhatsApp */}
              <div>
                <Label htmlFor="config-whatsapp">Número de WhatsApp</Label>
                <Input
                  id="config-whatsapp"
                  type="tel"
                  value={configForm.whatsapp_number}
                  onChange={(e) => setConfigForm({ ...configForm, whatsapp_number: e.target.value })}
                  placeholder="+54 9 11 1234-5678"
                />
              </div>

              {/* Pausa Total */}
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Pause className="h-4 w-4 text-orange-500" />
                  <div>
                    <p className="font-medium">Pausar Todo</p>
                    <p className="text-xs text-gray-500">Sin asignación ni notificaciones</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={configForm.is_paused}
                  onChange={(e) => setConfigForm({ ...configForm, is_paused: e.target.checked })}
                  className="w-4 h-4"
                />
              </div>

              {/* Razón de Pausa */}
              {configForm.is_paused && (
                <div>
                  <Label htmlFor="paused-reason">Razón de la pausa</Label>
                  <Input
                    id="paused-reason"
                    value={configForm.paused_reason}
                    onChange={(e) => setConfigForm({ ...configForm, paused_reason: e.target.value })}
                    placeholder="Ej: no asignar de momento"
                  />
                </div>
              )}

              {/* Pausa de Asignación */}
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <UserX className="h-4 w-4 text-blue-500" />
                  <div>
                    <p className="font-medium">Pausar Asignación</p>
                    <p className="text-xs text-gray-500">No recibe tickets nuevos</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={configForm.assignment_paused}
                  onChange={(e) => setConfigForm({ ...configForm, assignment_paused: e.target.checked })}
                  className="w-4 h-4"
                  disabled={configForm.is_paused}
                />
              </div>

              {/* Notificaciones */}
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  {configForm.notifications_enabled ? (
                    <Bell className="h-4 w-4 text-green-500" />
                  ) : (
                    <BellOff className="h-4 w-4 text-gray-400" />
                  )}
                  <div>
                    <p className="font-medium">Notificaciones</p>
                    <p className="text-xs text-gray-500">Alertas de WhatsApp</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={configForm.notifications_enabled}
                  onChange={(e) => setConfigForm({ ...configForm, notifications_enabled: e.target.checked })}
                  className="w-4 h-4"
                  disabled={configForm.is_paused}
                />
              </div>

              {/* Botones */}
              <div className="flex gap-2 justify-end pt-4 border-t">
                <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
                  <X className="h-4 w-4 mr-2" />
                  Cancelar
                </Button>
                <Button onClick={handleSaveConfig}>
                  <Save className="h-4 w-4 mr-2" />
                  Guardar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Operator Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Operador</DialogTitle>
            <DialogDescription>
              Actualiza el número de WhatsApp del operador
            </DialogDescription>
          </DialogHeader>
          {editingOperator && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Nombre</Label>
                <Input
                  id="name"
                  value={editingOperator.name}
                  disabled
                  className="bg-gray-100"
                />
              </div>
              <div>
                <Label htmlFor="whatsapp">Número de WhatsApp</Label>
                <Input
                  id="whatsapp"
                  type="tel"
                  value={editingOperator.whatsapp_number || ''}
                  onChange={(e) => setEditingOperator({ ...editingOperator, whatsapp_number: e.target.value })}
                  placeholder="+54 9 11 1234-5678"
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button onClick={handleSaveOperator}>
                  Guardar Cambios
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
