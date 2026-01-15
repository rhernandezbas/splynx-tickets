import { Navigate } from 'react-router-dom'

export function ProtectedRoute({ children, requiredRole }) {
  const isAuthenticated = sessionStorage.getItem('isAuthenticated') === 'true'
  const user = JSON.parse(sessionStorage.getItem('user') || '{}')

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole && user.role !== requiredRole) {
    // Si es operador intentando acceder a rutas de admin, redirigir a su vista
    if (user.role === 'operator') {
      return <Navigate to="/operator-view" replace />
    }
    // Si es admin intentando acceder a vista de operador, permitir
    return <Navigate to="/" replace />
  }

  return children
}

export function PublicRoute({ children }) {
  const isAuthenticated = sessionStorage.getItem('isAuthenticated') === 'true'
  const user = JSON.parse(sessionStorage.getItem('user') || '{}')

  if (isAuthenticated) {
    // Redirigir según el rol
    if (user.role === 'admin') {
      return <Navigate to="/" replace />
    } else if (user.role === 'operator') {
      return <Navigate to="/operator-view" replace />
    }
  }

  return children
}
