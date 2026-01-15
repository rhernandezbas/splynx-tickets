import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Operators from './pages/Operators'
import SchedulesEditable from './pages/SchedulesEditable'
import Configuration from './pages/Configuration'
import AuditLogs from './pages/AuditLogs'
import Messages from './pages/Messages'
import { Toaster } from './components/ui/toaster'

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="operators" element={<Operators />} />
          <Route path="schedules" element={<SchedulesEditable />} />
          <Route path="configuration" element={<Configuration />} />
          <Route path="messages" element={<Messages />} />
          <Route path="audit" element={<AuditLogs />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  )
}

export default App
