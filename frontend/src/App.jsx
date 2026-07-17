// Main App Component
// ===================

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'

// Pages
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Documents from './pages/Documents'
import Chat from './pages/Chat'
import Reports from './pages/Reports'
import Compare from './pages/Compare'
import Schedules from './pages/Schedules'

// Components
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'

// Layout for authenticated pages
function AuthenticatedLayout({ children }) {
  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

// Redirect if already authenticated
function PublicRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="loading-screen"><div className="spinner"></div></div>
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#1e1e2e',
              color: '#cdd6f4',
              border: '1px solid #45475a',
            },
          }}
        />
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={
            <PublicRoute><Login /></PublicRoute>
          } />
          <Route path="/signup" element={
            <PublicRoute><Signup /></PublicRoute>
          } />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Dashboard /></AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/analysis" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Analysis /></AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/documents" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Documents /></AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/chat" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Chat /></AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/reports" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Reports /></AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/compare" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Compare /></AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/schedules" element={
            <ProtectedRoute>
              <AuthenticatedLayout><Schedules /></AuthenticatedLayout>
            </ProtectedRoute>
          } />

          {/* Default Redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
