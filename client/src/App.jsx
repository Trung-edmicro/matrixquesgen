import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import GenerateExamPage from './pages/GenerateExamPage'
import ManageExamsPage from './pages/ManageExamsPage'
import MatrixLibraryPage from './pages/MatrixLibraryPage'
import CustomPromptsPage from './pages/CustomPromptsPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/generate" replace />} />
          <Route path="/generate" element={<GenerateExamPage />} />
          <Route path="/generate-custom" element={<CustomPromptsPage />} />
          <Route path="/manage" element={<ManageExamsPage />} />
          <Route path="/library" element={<MatrixLibraryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}

export default App
