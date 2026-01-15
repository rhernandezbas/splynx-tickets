# Frontend - Panel de Administración Splynx

Panel web moderno construido con React, Vite, TailwindCSS y shadcn/ui.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# Compilar para producción
npm run build

# Preview de producción
npm run preview
```

## 📁 Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/        # Componentes reutilizables
│   │   ├── ui/           # Componentes UI (shadcn/ui)
│   │   └── Layout.jsx    # Layout principal
│   ├── pages/            # Páginas de la aplicación
│   │   ├── Dashboard.jsx
│   │   ├── Operators.jsx
│   │   ├── Schedules.jsx
│   │   ├── Configuration.jsx
│   │   └── AuditLogs.jsx
│   ├── lib/              # Utilidades
│   │   ├── api.js        # Cliente API
│   │   └── utils.js      # Funciones auxiliares
│   ├── hooks/            # Custom hooks
│   │   └── use-toast.js
│   ├── App.jsx           # Componente principal
│   ├── main.jsx          # Entry point
│   └── index.css         # Estilos globales
├── public/               # Archivos estáticos
├── index.html           # HTML principal
├── vite.config.js       # Configuración Vite
├── tailwind.config.js   # Configuración Tailwind
└── package.json         # Dependencias
```

## 🎨 Componentes UI

Basados en shadcn/ui y Radix UI:
- Button
- Card
- Toast/Toaster
- Dialog
- Select
- Switch
- Tabs
- Label

## 🔌 API Client

El cliente API está en `src/lib/api.js`:

```javascript
import { adminApi } from '@/lib/api'

// Obtener operadores
const operators = await adminApi.getOperators()

// Pausar operador
await adminApi.pauseOperator(personId, { reason: 'Vacaciones' })

// Actualizar configuración
await adminApi.updateConfig('WHATSAPP_ENABLED', { value: 'true' })
```

## 🎯 Páginas

### Dashboard (`/`)
- Estadísticas generales
- Control del sistema
- Gráficos de distribución
- Tabla de operadores

### Operadores (`/operators`)
- Lista de operadores
- Pausar/Reanudar
- Control de notificaciones
- Ver horarios

### Horarios (`/schedules`)
- Horarios por operador
- Vista por día de semana
- Estado de horarios

### Configuración (`/configuration`)
- Parámetros del sistema
- Edición en tiempo real
- Categorías organizadas

### Auditoría (`/audit`)
- Registro de cambios
- Filtros avanzados
- Trazabilidad completa

## 🛠️ Desarrollo

### Agregar nueva página

1. Crear archivo en `src/pages/`:
```jsx
// src/pages/NewPage.jsx
export default function NewPage() {
  return <div>Nueva Página</div>
}
```

2. Agregar ruta en `App.jsx`:
```jsx
<Route path="new-page" element={<NewPage />} />
```

3. Agregar navegación en `Layout.jsx`:
```jsx
{ name: 'Nueva Página', href: '/new-page', icon: Icon }
```

### Agregar nuevo componente UI

```bash
# Los componentes UI están en src/components/ui/
# Seguir el patrón de shadcn/ui
```

### Llamar API

```javascript
import { adminApi } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

const { toast } = useToast()

try {
  const response = await adminApi.getOperators()
  // Usar response.data
} catch (error) {
  toast({
    title: 'Error',
    description: error.message,
    variant: 'destructive'
  })
}
```

## 🎨 Estilos

### TailwindCSS

```jsx
<div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
  <Button className="bg-primary text-white">Click</Button>
</div>
```

### Variables CSS

Definidas en `src/index.css`:
- `--primary`
- `--secondary`
- `--destructive`
- `--muted`
- etc.

### Utilidad `cn()`

```jsx
import { cn } from '@/lib/utils'

<div className={cn(
  "base-classes",
  isActive && "active-classes",
  className
)} />
```

## 📦 Build

```bash
# Desarrollo
npm run dev

# Producción
npm run build
# Output: dist/

# Preview
npm run preview
```

## 🔧 Configuración

### Vite (`vite.config.js`)
- Alias `@` apunta a `src/`
- Proxy `/api` al backend
- Puerto 3000

### Tailwind (`tailwind.config.js`)
- Tema personalizado
- Colores del sistema
- Animaciones

### Variables de Entorno (`.env`)
```
VITE_API_URL=http://localhost:5605
```

## 🚀 Deploy

### Opción 1: Estático (Nginx)
```bash
npm run build
# Copiar dist/ a servidor web
```

### Opción 2: Docker
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

### Opción 3: Vercel/Netlify
```bash
# Conectar repositorio
# Build command: npm run build
# Output directory: dist
```

## 📝 Notas

- React 18 con hooks
- Vite para build rápido
- TailwindCSS para estilos
- Recharts para gráficos
- Axios para HTTP
- React Router para navegación
