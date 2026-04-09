import { useEffect, useState } from 'react'

export default function Toast({ id, type = 'info', title, message, duration = 4000, onClose }) {
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    console.log(`🍞 Toast created [${type}] - id: ${id}, duration: ${duration}, title: ${title}, message: ${message}`)
    
    if (duration === 0) return

    const timer = setTimeout(() => {
      console.log(`⏰ Toast auto-closing [${type}] - id: ${id}`)
      setIsExiting(true)
      setTimeout(() => onClose(id), 300) // Animation delay
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, id, onClose, type, title, message])

  const typeStyles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  }

  const iconStyles = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ⓘ',
  }

  const iconColors = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-yellow-600',
    info: 'text-blue-600',
  }

  return (
    <div
      className={`
        transform transition-all duration-300 ease-out
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
      `}
    >
      <div
        className={`
          flex items-start gap-3 px-4 py-3 rounded-lg border
          ${typeStyles[type]}
          backdrop-blur-sm shadow-lg
        `}
        role="alert"
      >
        <span className={`flex-shrink-0 font-bold text-lg ${iconColors[type]}`}>
          {iconStyles[type]}
        </span>
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="font-semibold text-sm">{title}</h3>
          )}
          <p className={`text-sm ${title ? 'mt-1' : ''}`}>
            {message}
          </p>
        </div>
        <button
          onClick={() => {
            setIsExiting(true)
            setTimeout(() => onClose(id), 300)
          }}
          className={`
            flex-shrink-0 text-lg leading-none opacity-60 hover:opacity-100
            transition-opacity duration-200
          `}
          aria-label="Đóng thông báo"
        >
          ✕
        </button>
      </div>
    </div>
  )
}
