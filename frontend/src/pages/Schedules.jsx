import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, Clock } from 'lucide-react'

export default function Schedules() {
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

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

  const getDayName = (day) => {
    const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    return days[day]
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
                  <div className="text-right">
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
                </div>
              </CardHeader>
              <CardContent>
                {operator.schedules && operator.schedules.length > 0 ? (
                  <div className="space-y-3">
                    {[0, 1, 2, 3, 4, 5, 6].map((day) => {
                      const daySchedules = groupedSchedules[day] || []
                      return (
                        <div key={day} className="flex items-center justify-between py-2 border-b last:border-0">
                          <div className="font-medium text-sm w-32">
                            {getDayName(day)}
                          </div>
                          <div className="flex-1">
                            {daySchedules.length > 0 ? (
                              <div className="flex flex-wrap gap-2">
                                {daySchedules.map((schedule) => (
                                  <span
                                    key={schedule.id}
                                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                      schedule.is_active
                                        ? 'bg-blue-100 text-blue-800'
                                        : 'bg-gray-100 text-gray-800'
                                    }`}
                                  >
                                    {schedule.start_time} - {schedule.end_time}
                                  </span>
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
          <p>• Los horarios se configuran por día de la semana (0=Lunes, 6=Domingo)</p>
          <p>• Formato de hora: HH:MM (24 horas)</p>
          <p>• Los operadores solo reciben asignaciones durante sus horarios activos</p>
          <p>• Fin de semana: Solo el operador de guardia trabaja (9:00-21:00)</p>
        </CardContent>
      </Card>
    </div>
  )
}
