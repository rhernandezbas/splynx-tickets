Feature: Gestión de operadores
  Como administrador
  Quiero gestionar la configuración y horarios de los operadores
  Para controlar la asignación de tickets y las notificaciones

  Background:
    Given el usuario está autenticado como admin
    And la API admin está accesible en /api/admin

  @status:implemented
  Scenario: Listar operadores
    Given existen operadores configurados en operator_config
    When se hace GET a /api/admin/operators
    Then se retorna la lista de operadores con su configuración
    And cada operador incluye person_id, name, whatsapp_number, estados de pausa

  @status:implemented
  Scenario: Crear nuevo operador
    Given se proporciona person_id, name y whatsapp_number
    When se hace POST a /api/admin/operators con los datos
    Then se crea el operador en operator_config
    And se retorna el operador creado con is_active = True

  @status:implemented
  Scenario: Pausar operador completamente
    Given existe un operador activo con person_id
    When se hace POST a /api/admin/operators/{id}/pause
    Then el operador queda con is_paused = True
    And no recibe nuevas asignaciones
    And no recibe notificaciones WhatsApp
    And se registra paused_reason y paused_at

  @status:implemented
  Scenario: Pausar solo asignaciones de operador
    Given existe un operador activo con person_id
    When se pausa solo las asignaciones del operador
    Then el operador queda con assignment_paused = True
    And no recibe nuevas asignaciones
    But mantiene sus tickets actuales
    And sigue recibiendo notificaciones si notifications_enabled = True

  @status:implemented
  Scenario: Reanudar operador
    Given existe un operador pausado
    When se hace POST a /api/admin/operators/{id}/resume
    Then el operador queda con is_paused = False
    And vuelve a recibir asignaciones y notificaciones

  @status:implemented
  Scenario: Configurar horarios de operador
    Given existe un operador con person_id
    When se hace POST a /api/admin/schedules con horarios
    Then se crean los horarios en operator_schedule
    And se pueden configurar tres tipos: work, assignment, alert
    And cada horario tiene day_of_week, start_time, end_time

  @status:implemented
  Scenario: Modificar configuración global del sistema
    Given el usuario es admin
    When se hace POST a /api/admin/config con pares clave-valor
    Then se actualizan los valores en system_config
    And los cambios toman efecto cuando el cache de ConfigHelper se invalida

  @status:implemented
  Scenario: Pausar sistema completo
    Given el sistema está activo
    When se hace POST a /api/admin/system/pause
    Then todos los jobs dejan de procesar tickets
    And se puede reanudar con POST a /api/admin/system/resume

  @status:implemented
  Scenario: Operador sin rol admin no accede a admin
    Given el usuario está autenticado como operator
    When intenta acceder a cualquier endpoint /api/admin/*
    Then recibe respuesta 403 Forbidden
