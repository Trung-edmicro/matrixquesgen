import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import GenerateExamPage from './pages/GenerateExamPage'
import ManageExamsPage from './pages/ManageExamsPage'
import MatrixLibraryPage from './pages/MatrixLibraryPage'
import CustomPromptsPage from './pages/CustomPromptsPage'
import SettingsPage from './pages/SettingsPage'
import SoluteExamPage from './pages/SoluteExamPage'
import { NotificationProvider } from './context/NotificationContext'
import ToastContainer from './components/notifications/ToastContainer'

function App() {
  return (
    <NotificationProvider>
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/" element={<Navigate to="/generate" replace />} />
            <Route path="/generate" element={<GenerateExamPage />} />
            <Route path="/generate-custom" element={<CustomPromptsPage />} />
            <Route path = "/exam-extraction" element= {<SoluteExamPage/>} />
            <Route path="/manage" element={<ManageExamsPage />} />
            <Route path="/library" element={<MatrixLibraryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </AppLayout>
        <ToastContainer />
      </BrowserRouter>
    </NotificationProvider>
  )
}

export default App
