import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './components/layout/DashboardLayout'

const SignupPage = lazy(() => import('./pages/auth/SignupPage'))
const LoginPage = lazy(() => import('./pages/auth/LoginPage'))
const DashboardPage = lazy(() => import('./pages/dashboard/DashboardPage'))
const KeywordsPage = lazy(() => import('./pages/settings/KeywordsPage'))
const AlertsPage = lazy(() => import('./pages/settings/AlertsPage'))
const AnalyticsPage = lazy(() => import('./pages/analytics/AnalyticsPage'))
const SourcesPage = lazy(() => import('./pages/admin/SourcesPage'))
const OrganizationsPage = lazy(() => import('./pages/admin/OrganizationsPage'))

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  )
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="keywords" element={<KeywordsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="admin/sources" element={<SourcesPage />} />
          <Route path="admin/organizations" element={<OrganizationsPage />} />
          <Route path="settings/alerts" element={<AlertsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  )
}

export default App
