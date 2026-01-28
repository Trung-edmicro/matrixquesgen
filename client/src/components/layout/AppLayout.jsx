import { useState } from 'react'
import Header from './Header'
import Sidebar from './Sidebar'

export default function AppLayout({ children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          collapsed={sidebarCollapsed} 
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
        />
        
        <main className="flex-1 overflow-hidden bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  )
}
