Feature: Ciclo de vida de tickets
  Como sistema automatizado
  Quiero gestionar el ciclo completo de tickets desde recepción por webhook hasta cierre
  Para garantizar que todos los tickets se procesen y asignen correctamente

  Background:
    Given el sistema está activo y no pausado
    And la base de datos está accesible
    And el scheduler está ejecutándose dentro del horario laboral

  @status:deprecated
  @changed:2026-03-01
  @reason:Reemplazado por webhooks (ADR-003). Selenium ya no se usa.
  Scenario: Descarga de tickets desde Gestión Real
    Given Gestión Real está accesible
    And las credenciales de Selenium son válidas
    When se ejecuta el job de descarga de CSV
    Then se descargan los tickets nuevos desde Gestión Real
    And se almacenan en la tabla tickets_detection
    And se marcan con is_from_gestion_real = True

  @status:implemented
  @changed:2026-03-01
  @reason:Nuevo escenario que reemplaza la descarga por Selenium
  Scenario: Recepción de tickets por webhook
    Given Suricata envía un POST a /api/hooks/nuevo-ticket
    And el payload contiene campos con nombres con espacios (ej: "Numero de ticket")
    And el endpoint normaliza los campos a snake_case antes de guardar
    And el payload contiene numero_ticket (numérico) y numero_cliente (requerido)
    When el endpoint recibe el webhook
    Then se guarda el registro en la tabla hook_nuevo_ticket con processed = False
    And se responde con HTTP 200 y el ID del registro

  @status:implemented
  @changed:2026-03-01
  @reason:Nuevo escenario de procesamiento diferido de webhooks
  Scenario: Procesamiento de webhooks pendientes
    Given existen registros en hook_nuevo_ticket con processed = False
    When se ejecuta el job process_webhooks cada 3 minutos
    Then solo se procesan webhooks con motivo_contacto = "General Soporte"
    And los webhooks de otros motivos se marcan como processed sin crear ticket
    And se mapean los campos del webhook a tickets_detection
    And se crea un registro con Estado = PENDING e is_created_splynx = False
    And se marca el webhook como processed = True con timestamp
    And los webhooks duplicados se marcan como procesados sin crear nuevo registro

  @status:implemented
  Scenario: Creación de tickets en Splynx
    Given existen tickets en tickets_detection sin crear en Splynx
    And la API de Splynx está accesible
    When se ejecuta el job de creación de tickets
    Then se crean los tickets en Splynx con el Asunto prefijado con "GR"
    And se actualiza is_created_splynx = True
    And se registra el Ticket_ID de Splynx

  @status:implemented
  Scenario: Asignación automática de tickets
    Given existen tickets creados sin asignar
    And hay operadores disponibles en horario de asignación
    When se ejecuta el job de asignación
    Then se asigna cada ticket al operador con menos tickets
    And se actualiza el assignment_tracker del operador
    And se envía notificación WhatsApp al operador asignado

  @status:implemented
  Scenario: Asignación por tag de turno tarde
    Given existe un ticket con nota que contiene "[TT]"
    And los operadores de turno tarde (IDs 27, 38) están disponibles
    When se ejecuta la asignación
    Then el ticket se asigna a uno de los operadores de turno tarde
    And no se considera a operadores de turno día

  @status:implemented
  Scenario: Asignación por tag de turno día
    Given existe un ticket con nota que contiene "[TD]"
    And los operadores de turno día (IDs 10, 37) están disponibles
    When se ejecuta la asignación
    Then el ticket se asigna a uno de los operadores de turno día

  @status:implemented
  Scenario: Asignación en fin de semana
    Given es sábado o domingo
    And el operador de guardia (ID 10) está activo
    When se ejecuta la asignación
    Then todos los tickets se asignan al operador de guardia

  @status:implemented
  Scenario: Alerta de tickets vencidos
    Given un ticket tiene más de 45 minutos sin actualización
    And el operador asignado tiene notifications_enabled = True
    And el operador está dentro de su horario de alertas
    When se ejecuta el job de alertas
    Then se envía una alerta WhatsApp agrupada al operador
    And se incrementa el alert_count del ticket

  @status:implemented
  Scenario: Notificación de fin de turno
    Given falta 1 hora para el fin del turno de un operador
    And el operador tiene tickets abiertos asignados
    When se ejecuta el job de fin de turno
    Then se envía un resumen WhatsApp con los tickets pendientes del operador

  @status:implemented
  Scenario: Auto-desasignación después del turno
    Given el turno de un operador terminó hace más de 1 hora
    And el operador tiene tickets abiertos asignados
    When se ejecuta el job de auto-desasignación
    Then los tickets se desasignan del operador
    And quedan disponibles para reasignación

  @status:implemented
  Scenario: Sincronización de estado con Splynx
    Given existen tickets en la base de datos local
    And la API de Splynx está accesible
    When se ejecuta el job de sincronización
    Then se actualizan los estados de los tickets locales según Splynx
    And los tickets cerrados en Splynx se marcan como is_closed = True

  @status:deprecated
  @changed:2026-03-01
  @reason:Reemplazado por process_webhooks_job (ADR-003)
  Scenario: Flujo completo automático
    Given el scheduler ejecuta el job all_flow cada 3 minutos
    When se activa el job
    Then se ejecuta descarga de CSV
    And se crean tickets en Splynx
    And se asignan tickets no asignados
    And todo se ejecuta en un thread de background

  @status:implemented
  @changed:2026-03-01
  @reason:Nuevo escenario que reemplaza al flujo all_flow
  Scenario: Flujo automático por webhooks
    Given el scheduler ejecuta el job process_webhooks cada 3 minutos
    When se activa el job
    Then se procesan webhooks pendientes de hook_nuevo_ticket
    And se crean tickets en Splynx para los nuevos registros
    And todo se ejecuta en un thread de background

  @status:implemented
  Scenario: Sistema pausado no procesa tickets
    Given el sistema está pausado via SystemControl
    When se ejecuta cualquier job de tickets
    Then no se procesan tickets
    And se loguea que el sistema está pausado

  @status:implemented
  @changed:2026-03-01
  Scenario: Webhook de cierre de ticket (auditoría)
    Given Suricata envía un POST a /api/hooks/cierre-ticket
    When el endpoint recibe el webhook de cierre
    Then se guarda el registro en la tabla hook_cierre_ticket
    And no se cierra el ticket automáticamente en el sistema
    And la sincronización con Splynx es la fuente de verdad para cierres
