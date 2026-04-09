import { createContext, useCallback, useState } from 'react'

export const NotificationContext = createContext()

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([])

  const addNotification = useCallback((message, options = {}) => {
    const {
      type = 'info',
      title = '',
      duration = 4000,
    } = options

    const id = Date.now() + Math.random()
    
    console.log(`📢 addNotification called - type: ${type}, title: ${title}, message: ${message}, duration: ${duration}, id: ${id}`)

    setNotifications(prev => [...prev, {
      id,
      type,
      title,
      message,
      duration,
    }])

    return id
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const notify = useCallback((message, options = {}) => {
    return addNotification(message, { type: 'info', ...options })
  }, [addNotification])

  const success = useCallback((message, title = 'Thành công') => {
    return addNotification(message, { type: 'success', title, duration: 3000 })
  }, [addNotification])

  const error = useCallback((message, title = 'Lỗi') => {
    return addNotification(message, { type: 'error', title, duration: 5000 })
  }, [addNotification])

  const warning = useCallback((message, title = 'Cảnh báo') => {
    return addNotification(message, { type: 'warning', title, duration: 4000 })
  }, [addNotification])

  const info = useCallback((message, title = 'Thông tin') => {
    return addNotification(message, { type: 'info', title, duration: 4000 })
  }, [addNotification])

  const clear = useCallback(() => {
    setNotifications([])
  }, [])

  const value = {
    notifications,
    addNotification,
    removeNotification,
    notify,
    success,
    error,
    warning,
    info,
    clear,
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}
