import { Navigate, Route, Routes } from 'react-router-dom'
import { DashboardPage } from '../pages/DashboardPage'
import { LoginPage } from '../pages/LoginPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/nodes/enroll" element={<PlaceholderPage title="Node Enrollment" />} />
      <Route path="/nodes/registry" element={<PlaceholderPage title="Node Registry" />} />
      <Route path="/session/reset" element={<PlaceholderPage title="Session Reset" />} />
      <Route path="/logs/verification" element={<PlaceholderPage title="Verification Log" />} />
      <Route path="/logs/rejection" element={<PlaceholderPage title="Rejection Log" />} />
      <Route path="/merkle" element={<PlaceholderPage title="Merkle Batches" />} />
      <Route path="/anchors" element={<PlaceholderPage title="Blockchain Anchors" />} />
      <Route path="/workspace" element={<PlaceholderPage title="Verification Workspace" />} />
      <Route path="/exports" element={<PlaceholderPage title="Export" />} />
      <Route path="/status" element={<PlaceholderPage title="System Status" />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
