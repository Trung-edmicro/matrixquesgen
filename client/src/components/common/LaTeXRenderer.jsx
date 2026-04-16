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

  // Helper function to decode HTML entities
  const decodeHtmlEntities = (text) => {
    const textArea = document.createElement('textarea')
    textArea.innerHTML = text
    return textArea.value
  }

  // Helper function to add text with line breaks support
  const addTextWithLineBreaks = (container, text) => {
    // Decode HTML entities
    text = decodeHtmlEntities(text)
    
    // Split by newlines, but trim each line to avoid weird spacing
    const lines = text.split('\n')
    lines.forEach((line, index) => {
      if (index > 0) {
        container.appendChild(document.createElement('br'))
      }
      // Trim line to avoid leading/trailing whitespace but preserve content whitespace
      line = line.trim()
      if (line) {
        // Replace multiple spaces with single space to prevent concatenation issues
        line = line.replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ')
        const textNode = document.createTextNode(line)
        container.appendChild(textNode)
      }
    })
  }

  const renderLatex = () => {
    if (!containerRef.current) return

    const container = containerRef.current
    let text = typeof children === 'string' ? children : ''
    
    // Decode HTML entities first for the entire text
    text = decodeHtmlEntities(text)
    
    // Clear existing content
    container.innerHTML = ''

    // Improved pattern: handle $ ... $ patterns more carefully
    // Match inline (\$text\$) or display (\$\$text\$\$) but be more flexible
    const pattern = /\$\$([^\$]*?)\$\$|\$([^\$]*?)\$/g
    let lastIndex = 0
    let match

    try {
      while ((match = pattern.exec(text)) !== null) {
        // Add text before the match (with line break handling)
        if (match.index > lastIndex) {
          addTextWithLineBreaks(container, text.substring(lastIndex, match.index))
        }

        const isDisplay = match[0].startsWith('$$')
        const formula = isDisplay ? match[1].trim() : match[2].trim()
        
        // Skip empty formulas
        if (!formula) {
          lastIndex = match.index + match[0].length
          continue
        }

        // Create span for LaTeX
        const span = document.createElement('span')
        span.classList.add('latex-formula')
        span.style.display = isDisplay ? 'block' : 'inline'
        span.style.margin = isDisplay ? '0.5em 0' : '0 0.2em'
        
        try {
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
    } catch (e) {
      // If regex fails, just show plain text
      addTextWithLineBreaks(container, text)
      return
    }

    // Add remaining text (with line break handling)
    if (lastIndex < text.length) {
      addTextWithLineBreaks(container, text.substring(lastIndex))
    } else if (lastIndex === 0 && text) {
      // If no LaTeX found at all, just add the text with line breaks
      addTextWithLineBreaks(container, text)
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
      style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
    />
  )
}

/**
 * Simpler component for non-editable LaTeX
 */
export function LaTeX({ children, className = '' }) {
  return <LaTeXRenderer className={className}>{children}</LaTeXRenderer>
}
