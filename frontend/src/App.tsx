import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
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
import ComputerPage from './pages/ComputerPage'
import ProtectedRoute from './components/auth/ProtectedRoute'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      retry: 1,
    },
  },
})

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
                <Route path="memory" element={<MemoryPage />} />
                <Route path="documents" element={<DocumentsPage />} />
                <Route path="computer" element={<ComputerPage />} />
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
