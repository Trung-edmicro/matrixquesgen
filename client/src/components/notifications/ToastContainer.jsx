import { useContext } from 'react'
import Toast from './Toast'
import { NotificationContext } from '../../context/NotificationContext'

export default function ToastContainer() {
  const { notifications, removeNotification } = useContext(NotificationContext)

  console.log('🔔 ToastContainer render - notifications count:', notifications.length, 'notifications:', notifications)

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 max-w-md">
      {notifications.map(notification => (
        <Toast
          key={notification.id}
          id={notification.id}
          type={notification.type}
          title={notification.title}
          message={notification.message}
          duration={notification.duration}
          onClose={removeNotification}
        />
      ))}
    </div>
  )
}
