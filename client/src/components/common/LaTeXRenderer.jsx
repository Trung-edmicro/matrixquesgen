import { useEffect, useRef } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

/**
 * Component renders text with LaTeX formulas
 * Supports inline LaTeX: $formula$ and display LaTeX: $$formula$$
 */
export default function LaTeXRenderer({ children, className = '', contentEditable = false, onBlur = null }) {
  const containerRef = useRef(null)
  const originalContentRef = useRef(children)

  useEffect(() => {
    originalContentRef.current = children
    renderLatex()
  }, [children])

  const renderLatex = () => {
    if (!containerRef.current) return

    const container = containerRef.current
    let text = typeof children === 'string' ? children : ''
    
    // Clear existing content
    container.innerHTML = ''

    // Pattern to match $...$ (inline) and $$...$$ (display)
    // Use negative lookbehind to avoid matching \$
    const pattern = /(?<!\\)\$\$([^\$]+)\$\$|(?<!\\)\$([^\$]+)\$/g
    let lastIndex = 0
    let match

    while ((match = pattern.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        const textNode = document.createTextNode(text.substring(lastIndex, match.index))
        container.appendChild(textNode)
      }

      // Create span for LaTeX
      const span = document.createElement('span')
      span.classList.add('latex-formula')
      
      try {
        const isDisplay = match[0].startsWith('$$')
        const formula = isDisplay ? match[1] : match[2]
        
        katex.render(formula, span, {
          displayMode: isDisplay,
          throwOnError: false,
          errorColor: '#cc0000',
          strict: false,
          trust: true,
          macros: {
            '\\frac': '\\dfrac', // Use display-style fractions by default
          }
        })
      } catch (e) {
        // If error, show original text
        span.textContent = match[0]
        span.style.color = '#cc0000'
        span.title = 'LaTeX Error: ' + e.message
      }
      
      container.appendChild(span)
      lastIndex = match.index + match[0].length
    }

    // Add remaining text
    if (lastIndex < text.length) {
      const textNode = document.createTextNode(text.substring(lastIndex))
      container.appendChild(textNode)
    }

    // If no LaTeX found, just add the text
    if (lastIndex === 0 && text) {
      container.textContent = text
    }
  }

  const handleBlur = (e) => {
    if (onBlur) {
      // Get plain text content (without HTML)
      const text = e.target.innerText || e.target.textContent
      onBlur({ target: { textContent: text } })
    }
  }

  const handleFocus = (e) => {
    // When focusing for edit, show raw text with LaTeX syntax
    if (contentEditable) {
      e.target.textContent = originalContentRef.current
    }
  }

  const handleBlurLocal = (e) => {
    // Re-render LaTeX after editing
    if (contentEditable) {
      renderLatex()
    }
    handleBlur(e)
  }

  return (
    <span
      ref={containerRef}
      className={`latex-renderer ${className}`}
      contentEditable={contentEditable}
      suppressContentEditableWarning
      onFocus={handleFocus}
      onBlur={handleBlurLocal}
    />
  )
}

/**
 * Simpler component for non-editable LaTeX
 */
export function LaTeX({ children, className = '' }) {
  return <LaTeXRenderer className={className}>{children}</LaTeXRenderer>
}
