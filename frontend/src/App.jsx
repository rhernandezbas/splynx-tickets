import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Operators from './pages/Operators'
import SchedulesEditable from './pages/SchedulesEditable'
import Configuration from './pages/Configuration'
import AuditLogs from './pages/AuditLogs'
import Messages from './pages/Messages'
import Metrics from './pages/Metrics'
import OperatorView from './pages/OperatorView'
import Login from './pages/Login'
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute'
import { Toaster } from './components/ui/toaster'

function App() {
  return (
    <>
      <Routes>
        {/* Ruta pública de login */}
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />

        {/* Rutas protegidas para admin */}
        <Route path="/" element={
          <ProtectedRoute requiredRole="admin">
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="operators" element={<Operators />} />
          <Route path="schedules" element={<SchedulesEditable />} />
          <Route path="configuration" element={<Configuration />} />
          <Route path="messages" element={<Messages />} />
          <Route path="metrics" element={<Metrics />} />
          <Route path="audit" element={<AuditLogs />} />
        </Route>

        {/* Ruta protegida para operadores */}
        <Route path="/operator-view" element={
          <ProtectedRoute requiredRole="operator">
            <OperatorView />
          </ProtectedRoute>
        } />
      </Routes>
      <Toaster />
    </>
  )
}

export default App
