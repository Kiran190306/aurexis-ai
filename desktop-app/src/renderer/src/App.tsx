import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './components/providers/ThemeProvider'
import { AuthProvider } from './components/providers/AuthProvider'
import Layout from './components/layout/Layout'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ConversationsPage from './pages/ConversationsPage'
import ConversationDetailPage from './pages/ConversationDetailPage'
import SettingsPage from './pages/SettingsPage'
import ToolsPage from './pages/ToolsPage'
import AgentsPage from './pages/AgentsPage'
import MemoryPage from './pages/MemoryPage'
import DocumentsPage from './pages/DocumentsPage'
import AgentDashboardPage from './pages/AgentDashboardPage'
import VisionPage from './pages/VisionPage'
import VoicePage from './pages/VoicePage'
import ComputerPage from './pages/ComputerPage'
import ProtectedRoute from './components/auth/ProtectedRoute'
import { queryClient } from './services/query-client'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="conversations" element={<ConversationsPage />} />
                <Route path="conversations/:id" element={<ConversationDetailPage />} />
                <Route path="tools" element={<ToolsPage />} />
                <Route path="agents" element={<AgentsPage />} />
                <Route path="agent-dashboard" element={<AgentDashboardPage />} />
                <Route path="vision" element={<VisionPage />} />
                <Route path="voice" element={<VoicePage />} />
                <Route path="computer" element={<ComputerPage />} />
                <Route path="memory" element={<MemoryPage />} />
                <Route path="documents" element={<DocumentsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
