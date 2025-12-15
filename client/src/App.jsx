import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import GenerateExamPage from './pages/GenerateExamPage'
import ManageExamsPage from './pages/ManageExamsPage'
import MatrixLibraryPage from './pages/MatrixLibraryPage'
import TestPreview from './components/generate/TestPreview'

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/generate" replace />} />
          <Route path="/generate" element={<GenerateExamPage />} />
          <Route path="/manage" element={<ManageExamsPage />} />
          <Route path="/library" element={<MatrixLibraryPage />} />
          <Route path="/test-preview" element={<TestPreview />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}

export default App
