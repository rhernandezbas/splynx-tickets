import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/hooks/use-toast'
import { Users as UsersIcon, Plus, Edit2, Trash2, Key, RefreshCw } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function Users() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [resetPasswordUser, setResetPasswordUser] = useState(null)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    email: '',
    role: 'operator'
  })
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [resetPasswordData, setResetPasswordData] = useState({
    new_password: '',
    confirm_password: ''
  })
  const { toast } = useToast()

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/api/auth/users`, {
        withCredentials: true
      })
      setUsers(response.data.users || [])
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Error al cargar usuarios',
        variant: 'destructive'
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleCreate = () => {
    setEditingUser(null)
    setFormData({
      username: '',
      password: '',
      full_name: '',
      email: '',
      role: 'operator'
    })
    setShowModal(true)
  }

  const handleEdit = (user) => {
    setEditingUser(user)
    setFormData({
      username: user.username,
      password: '',
      full_name: user.full_name || '',
      email: user.email || '',
      role: user.role
    })
    setShowModal(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (editingUser) {
        // Actualizar usuario
        await axios.put(`${API_BASE_URL}/api/auth/users/${editingUser.id}`, formData, {
          withCredentials: true
        })
        toast({
          title: 'Actualizado',
          description: 'Usuario actualizado correctamente'
        })
      } else {
        // Crear usuario
        if (!formData.password) {
          toast({
            title: 'Error',
            description: 'La contraseña es requerida',
            variant: 'destructive'
          })
          return
        }
        await axios.post(`${API_BASE_URL}/api/auth/users`, formData, {
          withCredentials: true
        })
        toast({
          title: 'Creado',
          description: 'Usuario creado correctamente'
        })
      }
      
      setShowModal(false)
      fetchUsers()
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al guardar usuario',
        variant: 'destructive'
      })
    }
  }

  const handleDelete = async (userId) => {
    if (!confirm('¿Estás seguro de eliminar este usuario?')) {
      return
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/auth/users/${userId}`, {
        withCredentials: true
      })
      toast({
        title: 'Eliminado',
        description: 'Usuario eliminado correctamente'
      })
      fetchUsers()
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al eliminar usuario',
        variant: 'destructive'
      })
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast({
        title: 'Error',
        description: 'Las contraseñas no coinciden',
        variant: 'destructive'
      })
      return
    }

    try {
      await axios.post(`${API_BASE_URL}/api/auth/change-password`, {
        old_password: passwordData.old_password,
        new_password: passwordData.new_password
      }, {
        withCredentials: true
      })
      
      toast({
        title: 'Actualizado',
        description: 'Contraseña actualizada correctamente'
      })
      
      setShowPasswordModal(false)
      setPasswordData({
        old_password: '',
        new_password: '',
        confirm_password: ''
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al cambiar contraseña',
        variant: 'destructive'
      })
    }
  }

  const handleResetPassword = (user) => {
    setResetPasswordUser(user)
    setResetPasswordData({
      new_password: '',
      confirm_password: ''
    })
    setShowResetPasswordModal(true)
  }

  const handleSubmitResetPassword = async (e) => {
    e.preventDefault()
    
    if (resetPasswordData.new_password !== resetPasswordData.confirm_password) {
      toast({
        title: 'Error',
        description: 'Las contraseñas no coinciden',
        variant: 'destructive'
      })
      return
    }

    try {
      await axios.post(`${API_BASE_URL}/api/auth/users/${resetPasswordUser.id}/reset-password`, {
        new_password: resetPasswordData.new_password
      }, {
        withCredentials: true
      })
      
      toast({
        title: 'Actualizado',
        description: `Contraseña de ${resetPasswordUser.username} actualizada correctamente`
      })
      
      setShowResetPasswordModal(false)
      setResetPasswordUser(null)
      setResetPasswordData({
        new_password: '',
        confirm_password: ''
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: error.response?.data?.error || 'Error al resetear contraseña',
        variant: 'destructive'
      })
    }
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
          <h1 className="text-3xl font-bold tracking-tight">Gestión de Usuarios</h1>
          <p className="text-muted-foreground">
            Administra los usuarios del sistema
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowPasswordModal(true)} variant="outline">
            <Key className="h-4 w-4 mr-2" />
            Cambiar mi Contraseña
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Usuario
          </Button>
        </div>
      </div>

      {/* Tabla de Usuarios */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UsersIcon className="h-5 w-5" />
            Usuarios del Sistema ({users.length})
          </CardTitle>
          <CardDescription>
            Lista de todos los usuarios con acceso al sistema
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-medium">Usuario</th>
                  <th className="text-left p-3 font-medium">Nombre Completo</th>
                  <th className="text-left p-3 font-medium">Email</th>
                  <th className="text-left p-3 font-medium">Rol</th>
                  <th className="text-left p-3 font-medium">Estado</th>
                  <th className="text-left p-3 font-medium">Último Login</th>
                  <th className="text-left p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b hover:bg-gray-50">
                    <td className="p-3 font-medium">{user.username}</td>
                    <td className="p-3">{user.full_name || '-'}</td>
                    <td className="p-3">{user.email || '-'}</td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {user.role === 'admin' ? 'Administrador' : 'Operador'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {user.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-gray-600">
                      {user.last_login ? new Date(user.last_login).toLocaleString() : 'Nunca'}
                    </td>
                    <td className="p-3">
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEdit(user)}
                          className="h-8 px-2"
                          title="Editar usuario"
                        >
                          <Edit2 className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleResetPassword(user)}
                          className="h-8 px-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                          title="Cambiar contraseña"
                        >
                          <Key className="h-3 w-3" />
                        </Button>
                        {user.username !== 'admin' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDelete(user.id)}
                            className="h-8 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                            title="Eliminar usuario"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Modal Crear/Editar Usuario */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Usuario</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                  disabled={editingUser !== null}
                />
              </div>
              
              {!editingUser && (
                <div>
                  <label className="block text-sm font-medium mb-1">Contraseña</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium mb-1">Nombre Completo</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Rol</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="operator">Operador</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
              
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  {editingUser ? 'Actualizar' : 'Crear'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Cambiar Contraseña */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Cambiar Contraseña</h2>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Contraseña Actual</label>
                <input
                  type="password"
                  value={passwordData.old_password}
                  onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Nueva Contraseña</label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Confirmar Nueva Contraseña</label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                />
              </div>
              
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowPasswordModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  Cambiar Contraseña
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Resetear Contraseña de Usuario */}
      {showResetPasswordModal && resetPasswordUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              Cambiar Contraseña de {resetPasswordUser.username}
            </h2>
            <form onSubmit={handleSubmitResetPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Nueva Contraseña</label>
                <input
                  type="text"
                  value={resetPasswordData.new_password}
                  onChange={(e) => setResetPasswordData({ ...resetPasswordData, new_password: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                  placeholder="Ingresa la nueva contraseña"
                />
                <p className="text-xs text-gray-500 mt-1">
                  La contraseña será visible para que puedas compartirla con el usuario
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Confirmar Nueva Contraseña</label>
                <input
                  type="text"
                  value={resetPasswordData.confirm_password}
                  onChange={(e) => setResetPasswordData({ ...resetPasswordData, confirm_password: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                  placeholder="Confirma la nueva contraseña"
                />
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                <p className="text-sm text-blue-800">
                  <strong>Nota:</strong> Asegúrate de compartir esta contraseña con el usuario de forma segura.
                </p>
              </div>
              
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowResetPasswordModal(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  Cambiar Contraseña
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
