import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'
import { RefreshCw, FileSearch, CheckCircle, AlertCircle, User, Clock, Trash2, XCircle, Check } from 'lucide-react'

export default function AuditTickets() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  const fetchAuditTickets = async () => {
    try {
      setLoading(true)
      const response = await adminApi.getAuditTickets()
      setTickets(response.data.tickets || [])
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar tickets para auditoría',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (ticketId) => {
    try {
      await adminApi.approveAudit(ticketId)
      toast({
        title: '✅ Auditoría aprobada',
        description: `Ticket #${ticketId} aprobado. Contadores de exceeded_threshold reseteados.`
      })
      fetchAuditTickets()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'No se pudo aprobar la auditoría',
        variant: 'destructive'
      })
    }
  }

  const handleReject = async (ticketId) => {
    try {
      await adminApi.rejectAudit(ticketId)
      toast({
        title: '⚠️ Auditoría rechazada',
        description: `Ticket #${ticketId} rechazado. No se modificaron contadores.`
      })
      fetchAuditTickets()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'No se pudo rechazar la auditoría',
        variant: 'destructive'
      })
    }
  }

  const handleDelete = async (ticketId) => {
    if (!confirm(`¿Estás seguro de eliminar este ticket de la vista de auditoría?`)) {
      return
    }
    
    try {
      await adminApi.deleteAudit(ticketId)
      toast({
        title: '👁️ Ticket ocultado',
        description: `Ticket #${ticketId} eliminado de la vista de auditoría.`
      })
      fetchAuditTickets()
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'No se pudo eliminar la auditoría'
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive'
      })
    }
  }

  useEffect(() => {
    fetchAuditTickets()
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchAuditTickets, 30000)
    return () => clearInterval(interval)
  }, [])

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
          <h1 className="text-3xl font-bold tracking-tight">Tickets para Auditoría</h1>
          <p className="text-muted-foreground">
            Tickets marcados por operadores para revisión manual
          </p>
        </div>
        <Button onClick={fetchAuditTickets} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <FileSearch className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{tickets.length}</div>
            <p className="text-xs text-muted-foreground">
              Solicitudes totales
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pendientes</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {tickets.filter(t => t.audit_status === 'pending').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Sin revisar
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aprobadas</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {tickets.filter(t => t.audit_status === 'approved').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Aprobadas
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rechazadas</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {tickets.filter(t => t.audit_status === 'rejected').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Rechazadas
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Tickets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSearch className="h-5 w-5" />
            Tickets Solicitados para Auditoría
          </CardTitle>
          <CardDescription>
            Tickets que requieren revisión manual del administrador
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tickets.length > 0 ? (
            <div className="space-y-3">
              {tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  className={`p-4 border rounded-lg transition-colors ${
                    ticket.audit_notified ? 'bg-gray-50 border-gray-200' : 'bg-orange-50 border-orange-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      {/* Header */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-sm font-semibold text-gray-700">
                          Ticket #{ticket.ticket_id}
                        </span>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.priority === 'Alta' ? 'bg-red-100 text-red-800' :
                          ticket.priority === 'Media' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {ticket.priority}
                        </span>
                        {ticket.exceeded_threshold && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            ⚠️ Vencido
                          </span>
                        )}
                        {/* Estado de auditoría */}
                        {ticket.audit_status === 'pending' && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                            ⏳ Pendiente
                          </span>
                        )}
                        {ticket.audit_status === 'approved' && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            ✅ Aprobado
                          </span>
                        )}
                        {ticket.audit_status === 'rejected' && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            ❌ Rechazado
                          </span>
                        )}
                      </div>

                      {/* Detalles */}
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-gray-900">{ticket.subject}</p>
                        <p className="text-sm text-gray-600">
                          <strong>Cliente:</strong> {ticket.customer_name || ticket.customer_id}
                        </p>
                      </div>

                      {/* Metadata */}
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          Operador ID: {ticket.audit_requested_by}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(ticket.audit_requested_at).toLocaleString('es-AR')}
                        </span>
                        {ticket.response_time_minutes && (
                          <span>
                            ⏱️ {ticket.response_time_minutes} min
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Acciones */}
                    <div className="flex flex-col gap-2">
                      {ticket.audit_status === 'pending' && (
                        <>
                          <Button
                            onClick={() => handleApprove(ticket.ticket_id)}
                            size="sm"
                            variant="default"
                            className="whitespace-nowrap bg-green-600 hover:bg-green-700"
                          >
                            <Check className="h-4 w-4 mr-1" />
                            Aprobar
                          </Button>
                          <Button
                            onClick={() => handleReject(ticket.ticket_id)}
                            size="sm"
                            variant="destructive"
                            className="whitespace-nowrap"
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            Rechazar
                          </Button>
                        </>
                      )}
                      <Button
                        onClick={() => handleDelete(ticket.ticket_id)}
                        size="sm"
                        variant="outline"
                        className="whitespace-nowrap text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Eliminar
                      </Button>
                      <Button
                        onClick={() => window.open(`https://splynx.ipnext.com.ar/admin/support/tickets/view/${ticket.ticket_id}`, '_blank')}
                        size="sm"
                        variant="outline"
                        className="whitespace-nowrap"
                      >
                        Ver en Splynx
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <FileSearch className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium">No hay tickets para auditoría</p>
              <p className="text-sm">Los operadores pueden marcar tickets vencidos para revisión manual</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Sobre la Auditoría de Tickets</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-blue-800 space-y-2">
          <p>• 🔍 Los operadores pueden marcar tickets vencidos para auditoría</p>
          <p>• ✅ <strong>Aprobar:</strong> Resetea contadores de exceeded_threshold y alertas</p>
          <p>• ❌ <strong>Rechazar:</strong> Solo marca como rechazado, no modifica contadores</p>
          <p>• 🗑️ <strong>Eliminar:</strong> Oculta de esta vista (requiere aprobar/rechazar primero)</p>
          <p>• 🔄 La lista se actualiza automáticamente cada 30 segundos</p>
          <p>• 🔗 Puedes abrir cada ticket directamente en Splynx para gestionarlo</p>
        </CardContent>
      </Card>
    </div>
  )
}
