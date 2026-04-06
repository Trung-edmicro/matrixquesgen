import { useMemo, useEffect, useRef, useState, useCallback } from 'react'
import LaTeXRenderer from './LaTeXRenderer'
import * as echarts from 'echarts'


/**
 * Component để render rich content (text, mixed với table/image/chart)
 * @param {Object} content - Content object với format {type: 'text'|'mixed', content: ...}
 * @param {boolean} contentEditable - Có cho phép chỉnh sửa không
 * @param {Function} onBlur - Callback khi blur (nếu contentEditable)
 * @param {string} className - Additional CSS classes
 * @param {string} questionCode - Question code for chart indexing (e.g., "C1", "C2")
 */
export default function RichContentRenderer({ content, contentEditable = false, onBlur, className = '', questionCode = '' }) {
  // Handle legacy string format
  if (typeof content === 'string') {
    return (
      <LaTeXRenderer
        contentEditable={contentEditable}
        onBlur={onBlur}
        className={className}
      >
        {content}
      </LaTeXRenderer>
    )
  }

  // Handle new rich content format
  if (!content || typeof content !== 'object') {
    return null
  }

  const { type, content: contentData } = content

  // Simple text content
  if (type === 'text') {
    return (
      <LaTeXRenderer
        contentEditable={contentEditable}
        onBlur={onBlur}
        className={className}
      >
        {contentData}
      </LaTeXRenderer>
    )
  }

  // Image content (single image)
  if (type === 'image') {
    if (!Array.isArray(contentData)) {
      return <div className="text-red-500">Invalid image content format</div>
    }

    return (
      <div className={`space-y-3 ${className}`}>
        {contentData.map((item, index) => {
          if (typeof item === 'string') {
            return (
              <LaTeXRenderer key={index} contentEditable={contentEditable} onBlur={onBlur}>
                {item}
              </LaTeXRenderer>
            )
          }

          if (typeof item === 'object' && item !== null && item.type === 'image') {
            return <ImageRenderer key={index} content={item.content} metadata={item.metadata} />
          }

          // Log unexpected items for debugging
          console.warn('Unexpected item in image content:', item)
          return null
        })}
      </div>
    )
  }

  // Table content (single table)
  if (type === 'table') {
    if (!Array.isArray(contentData)) {
      return <div className="text-red-500">Invalid table content format</div>
    }

    return (
      <div className={`space-y-3 ${className}`}>
        {contentData.map((item, index) => {
          if (typeof item === 'string') {
            return (
              <LaTeXRenderer key={index} contentEditable={contentEditable} onBlur={onBlur}>
                {item}
              </LaTeXRenderer>
            )
          }

          if (typeof item === 'object' && item.type === 'table') {
            return <TableRenderer key={index} content={item.content} metadata={item.metadata} />
          }

          return null
        })}
      </div>
    )
  }

  // Chart content (single chart)
  if (type === 'chart') {
    if (!Array.isArray(contentData)) {
      return <div className="text-red-500">Invalid chart content format</div>
    }

    let chartIndex = 0  // ✨ NEW: Track chart index for export identification
    
    return (
      <div className={`space-y-3 ${className}`}>
        {contentData.map((item, index) => {
          if (typeof item === 'string') {
            return (
              <LaTeXRenderer key={index} contentEditable={contentEditable} onBlur={onBlur}>
                {item}
              </LaTeXRenderer>
            )
          }

          if (typeof item === 'object' && item.type === 'chart') {
            // ✨ NEW: Pass questionCode and chart index to ChartRenderer
            const currChartIndex = chartIndex
            chartIndex++  // Increment for next chart
            return <ChartRenderer 
              key={index} 
              content={item.content} 
              metadata={item.metadata} 
              questionCode={questionCode}
              chartIndex={currChartIndex}
            />
          }

          return null
        })}
      </div>
    )
  }

  // Mixed content (text + tables + images + charts)
  if (type === 'mixed') {
    if (!Array.isArray(contentData)) {
      return <div className="text-red-500">Invalid mixed content format</div>
    }

    let chartIndex = 0  // ✨ NEW: Track chart index for export identification
    
    return (
      <div className={`space-y-3 ${className}`}>
        {contentData.map((item, index) => {
          if (typeof item === 'string') {
            return (
              <LaTeXRenderer key={index} contentEditable={contentEditable} onBlur={onBlur}>
                {item}
              </LaTeXRenderer>
            )
          }

          if (typeof item === 'object') {
            // Table content
            if (item.type === 'table') {
              return <TableRenderer key={index} content={item.content} metadata={item.metadata} />
            }

            // Image content
            if (item.type === 'image') {
              return <ImageRenderer key={index} content={item.content} metadata={item.metadata} />
            }

            // Chart content (ECharts)
            if (item.type === 'chart') {
              // ✨ NEW: Pass questionCode and chart index to ChartRenderer
              const currChartIndex = chartIndex
              chartIndex++  // Increment for next chart
              return <ChartRenderer 
                key={index} 
                content={item.content} 
                metadata={item.metadata} 
                questionCode={questionCode}
                chartIndex={currChartIndex}
              />
            }
          }

          return null
        })}
      </div>
    )
  }

  return <div className="text-gray-500">Unsupported content type: {type}</div>
}

/**
 * Component để render table từ JSON
 */
function TableRenderer({ content, metadata }) {
  const tableData = useMemo(() => {
    try {
      if (typeof content === 'string') {
        return JSON.parse(content)
      }
      return content
    } catch (e) {
      console.error('Failed to parse table content:', e)
      return null
    }
  }, [content])

  if (!tableData || !tableData.headers || !tableData.rows) {
    return <div className="text-red-500">Invalid table data</div>
  }

  const caption = metadata?.caption || ''
  const source = metadata?.source || ''

  return (
    <div className="overflow-x-auto my-3">
      {caption && (
        <div className="mb-1 text-center text-sm font-bold text-gray-700">
          <LaTeXRenderer>{caption}</LaTeXRenderer>
        </div>
      )}
      <table className="border-collapse border border-gray-300 text-sm table-auto w-full">
        <thead className="bg-gray-50">
          <tr>
            {tableData.headers.map((header, idx) => (
              <th
                key={idx}
                className="border border-gray-300 px-3 py-2 text-left font-medium text-gray-700"
              >
                <LaTeXRenderer>{header}</LaTeXRenderer>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, rowIdx) => (
            <tr key={rowIdx} className={rowIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="border border-gray-300 px-3 py-2">
                  <LaTeXRenderer>{cell}</LaTeXRenderer>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {source && (
        <div className="mt-0.5 text-right text-xs italic text-gray-500">
          <LaTeXRenderer>{`(Nguồn: ${source})`}</LaTeXRenderer>
        </div>
      )}
    </div>
  )
}

/**
 * Component để render image (local hoặc URL)
 */
function ImageRenderer({ content, metadata }) {
  const [imageError, setImageError] = useState(null)
  const [imageLoaded, setImageLoaded] = useState(false)
  
  const imageUrl = typeof content === 'string' ? content : content?.url || content?.content

  // Handle metadata as object or array
  const caption = metadata?.caption || metadata?.[0] || 'Question image'
  const description = metadata?.description
  
  // Debug logging
  useEffect(() => {
    console.log('ImageRenderer mounted:', { imageUrl, content, metadata })
  }, [imageUrl])
  
  if (imageError) {
    return (
      <div className="my-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
        <strong>❌ Failed to load image</strong><br/>
        <code className="text-xs bg-red-100 px-1 py-0.5 rounded">{imageUrl}</code><br/>
        <small className="text-red-600">{imageError}</small>
      </div>
    )
  }
  
  return (
    <div className="my-3 flex flex-col items-center">
      {!imageLoaded && (
        <div className="text-gray-400 text-sm italic">Loading image...</div>
      )}
      <img
        src={imageUrl}
        alt={caption}
        className="max-w-2xl w-full h-auto rounded border border-gray-200 shadow-sm"
        style={{ display: imageLoaded ? 'block' : 'none', maxHeight: '400px', objectFit: 'contain' }}
        onLoad={() => {
          console.log('✅ Image loaded:', imageUrl)
          setImageLoaded(true)
        }}
        onError={(e) => {
          console.error('❌ Failed to load image:', imageUrl, e)
          setImageError(`Cannot load image from: ${imageUrl}. Check that the server is running on port 8000.`)
        }}
      />
      {/* Caption */}
      {caption && imageLoaded && (
        <div className="text-sm text-gray-600 mt-2 italic text-center">
          <LaTeXRenderer>{caption}</LaTeXRenderer>
        </div>
      )}
      {/* Description (if available) - for debugging */}
      {/* {description && import.meta.env.DEV && imageLoaded && (
        <details className="text-xs text-gray-500 mt-1">
          <summary>Image description (dev only)</summary>
          <p className="mt-1">{description.substring(0, 200)}...</p>
        </details>
      )} */}
    </div>
  )
}

/**
 * Create pattern canvas function - dùng để tạo fills với patterns
 * Note: Này sẽ được export vào window scope để các formatter có thể dùng
 */
function createPattern(type) {
  let canvas = document.createElement('canvas')
  let ctx = canvas.getContext('2d')
  canvas.width = 16
  canvas.height = 16

  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, 16, 16)
  ctx.strokeStyle = '#000'
  ctx.fillStyle = '#000'
  ctx.lineWidth = 1

  if (type === 'dots') {
    // Chấm bi
    ctx.beginPath()
    ctx.arc(4, 4, 1.5, 0, Math.PI * 2)
    ctx.arc(12, 12, 1.5, 0, Math.PI * 2)
    ctx.fill()
  } else if (type === 'diagonal') {
    // Sọc chéo
    ctx.beginPath()
    ctx.moveTo(0, 16)
    ctx.lineTo(16, 0)
    ctx.moveTo(-8, 8)
    ctx.lineTo(8, -8)
    ctx.moveTo(8, 24)
    ctx.lineTo(24, 8)
    ctx.stroke()
  } else if (type === 'zigzag') {
    // Gợn sóng/Zigzag
    ctx.beginPath()
    ctx.moveTo(0, 4)
    ctx.lineTo(4, 0)
    ctx.lineTo(8, 4)
    ctx.lineTo(12, 0)
    ctx.lineTo(16, 4)
    ctx.moveTo(0, 12)
    ctx.lineTo(4, 8)
    ctx.lineTo(8, 12)
    ctx.lineTo(12, 8)
    ctx.lineTo(16, 12)
    ctx.stroke()
  } else if (type === 'cross') {
    // Caro
    ctx.fillStyle = '#ddd'
    ctx.fillRect(0, 0, 16, 16)
    ctx.strokeStyle = '#000'
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(16, 16)
    ctx.moveTo(16, 0)
    ctx.lineTo(0, 16)
    ctx.stroke()
  } else if (type === 'horizontal') {
    // Kẻ ngang
    for (let i = 4; i < 16; i += 3) {
      ctx.beginPath()
      ctx.moveTo(0, i)
      ctx.lineTo(16, i)
      ctx.stroke()
    }
  } else if (type === 'vertical') {
    // Kẻ dọc
    for (let i = 4; i < 16; i += 3) {
      ctx.beginPath()
      ctx.moveTo(i, 0)
      ctx.lineTo(i, 16)
      ctx.stroke()
    }
  } else if (type === 'grid') {
    // Lưới
    for (let i = 4; i < 16; i += 3) {
      ctx.beginPath()
      ctx.moveTo(0, i)
      ctx.lineTo(16, i)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(i, 0)
      ctx.lineTo(i, 16)
      ctx.stroke()
    }
  } else if (type === 'diagonal_reverse') {
    // Sọc chéo ngược
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(16, 16)
    ctx.moveTo(16, -8)
    ctx.lineTo(-8, 16)
    ctx.moveTo(24, 0)
    ctx.lineTo(8, 16)
    ctx.stroke()
  }

  return canvas
}

/**
 * Function để resolve placeholders trong ECharts option
 * Chuyển các string placeholder thành actual functions
 * 
 * Hỗ trợ các placeholder từ tất cả các loại chart:
 * - FORMATTER_PLACEHOLDER: Y-axis label formatter
 * - FORMATTER_LABEL_PLACEHOLDER_BAR: Bar chart label formatter
 * - FORMATTER_LABEL_PLACEHOLDER_PIE: Pie chart label formatter
 * - FORMATTER_LABEL_PLACEHOLDER: Line chart label formatter
 * - FORMATTER_SCATTER_LABEL_PLACEHOLDER: Scatter label formatter (Area chart)
 * - FORMATTER_X_PLACEHOLDER: Line chart X-axis formatter
 * - FORMATTER_X_INTERVAL_PLACEHOLDER: Bar/Area chart X-axis interval
 * - PATTERN_PLACEHOLDER_*: Pattern canvas for fills
 */
function resolveChartOptionPlaceholders(options) {
  if (!options || typeof options !== 'object') {
    return options
  }

  // Deep clone để tránh modify original
  const resolved = JSON.parse(JSON.stringify(options))

  // Get yAxis max value for FORMATTER_PLACEHOLDER
  const yAxisMax = resolved.yAxis?.max || 100
  const yAxisInterval = resolved.yAxis?.interval || 10
  const axisMaxDisplay = yAxisMax - (yAxisInterval * 0.5)

  // Helper: apply function recursively
  const applyFunctionReplacements = (obj) => {
    if (!obj || typeof obj !== 'object') return

    if (Array.isArray(obj)) {
      obj.forEach((item) => applyFunctionReplacements(item))
    } else {
      for (const [key, value] of Object.entries(obj)) {
        // Check for formatter placeholders
        if (key === 'formatter' && typeof value === 'string') {
          if (value === 'FORMATTER_PLACEHOLDER') {
            // Y-axis label formatter with rich text for fake tick marks
            // Returns: {value|NUMBER}{tick|} - draws the value + a fake tick mark
            obj[key] = function (value) {
              if (value > axisMaxDisplay) {
                return '' // Hide top tick (arrow tip)
              }
              // Return rich text: value + tick mark render as a small black line
              return '{value|' + value + '}{tick|}'
            }
          } else if (value === 'FORMATTER_LABEL_PLACEHOLDER_BAR') {
            // Label formatter cho bar chart - format number with comma
            obj[key] = function (params) {
              let val = params.value.toString().replace('.', ',')
              if (!val.includes(',')) val += ',0'
              return val
            }
          } else if (value === 'FORMATTER_LABEL_PLACEHOLDER_PIE') {
            // Label formatter cho pie chart - format number with comma
            obj[key] = function (params) {
              let val = params.value.toString().replace('.', ',')
              if (!val.includes(',')) val += ',0'
              return val
            }
          } else if (value === 'FORMATTER_LABEL_PLACEHOLDER') {
            // Label formatter cho line chart
            // Ẩn label tại index 0 (giao với trục tung), format số
            obj[key] = function (params) {
              if (params.dataIndex === 0) return '' // Hide label at origin
              let val = params.value.toString().replace('.', ',')
              if (!val.includes(',')) val += ',0'
              return val
            }
          } else if (value === 'FORMATTER_SCATTER_LABEL_PLACEHOLDER') {
            // Label formatter cho scatter labels (Area chart)
            // Dùng realValue từ params.data
            obj[key] = function (params) {
              let val = params.data.realValue.toString().replace('.', ',')
              if (!val.includes(',')) val += ',0'
              return val
            }
          } else if (value === 'FORMATTER_X_PLACEHOLDER') {
            // X-axis formatter cho line chart
            // Tạo rich text: tick trên + value dưới
            // Format: {tick|}\n{value|TEXT}
            const xCategories = resolved.xAxis?.data || []
            obj[key] = function (value, index) {
              if (index >= xCategories.length) {
                return '' // Hide top tick (arrow tip)
              }
              // Return rich text with tick above value
              return '{tick|}\n{value|' + value + '}'
            }
          } else if (value === 'FORMATTER_X_INTERVAL_PLACEHOLDER') {
            // X-axis interval cho bar/area chart - just mark for later handling
            // Will be replaced with 0 (show all labels) in special handling section
            obj[key] = 'FORMATTER_X_INTERVAL_PLACEHOLDER' // Keep as-is for now
          }
        }

        // ✨ Handle _patternType meta field - apply pattern to itemStyle AND areaStyle (for area charts)
        if (key === '_patternType' && typeof value === 'string') {
          // Create itemStyle if it doesn't exist
          if (!obj.itemStyle) {
            obj.itemStyle = {}
          }
          // Apply pattern config object to itemStyle (for line markers)
          obj.itemStyle.color = {
            type: 'pattern',
            image: createPattern(value),
            repeat: 'repeat'
          }
          
          // Also apply to areaStyle if it exists (for area charts)
          if (obj.areaStyle) {
            obj.areaStyle.color = {
              type: 'pattern',
              image: createPattern(value),
              repeat: 'repeat'
            }
          }
          
          // Remove meta field after processing
          delete obj[key]
        }

        // Check for pattern placeholders in itemStyle.color
        if (key === 'color' && typeof value === 'object' && value !== null) {
          if (value.image && typeof value.image === 'string' && value.image.startsWith('PATTERN_PLACEHOLDER_')) {
            const patternType = value.image.replace('PATTERN_PLACEHOLDER_', '')
            obj[key] = {
              ...value,
              image: createPattern(patternType)
            }
          }
        }

        // Recursive check trong nested objects
        if (typeof value === 'object' && value !== null) {
          applyFunctionReplacements(value)
        }
      }
    }
  }

  applyFunctionReplacements(resolved)

  // SPECIAL HANDLING: Fix X-axis labels for bar charts
  // Add formatter to hide "-" values and ensure labels display
  if (resolved.xAxis && resolved.xAxis.axisLabel) {
    const xAxisLabel = resolved.xAxis.axisLabel
    
    // If interval needs fixing
    if (xAxisLabel.interval === 'FORMATTER_X_INTERVAL_PLACEHOLDER') {
      xAxisLabel.interval = 0 // Show all labels
    }
    
    // Add formatter to hide "-" values if we have series data
    if (resolved.series && resolved.series[0] && !xAxisLabel.formatter) {
      const seriesData = resolved.series[0].data
      xAxisLabel.formatter = function(value, index) {
        // Hide empty placeholders for year gaps
        if (seriesData && seriesData[index] !== undefined && seriesData[index] !== null) {
          if (seriesData[index] === '-' || seriesData[index].toString().startsWith('_')) {
            return ''
          }
        }
        return value
      }
    }
  }

  console.log('✅ [ChartResolver] Resolved chart option ready for echarts')
  return resolved
}

/**
 * ✨ REWRITTEN: ChartRenderer v2.0
 * Completely redesigned to avoid dimension sync issues
 * 
 * Key changes:
 * - Direct canvas DOM sizing from bounding rect (no CSS state intermediary)
 * - Single ResizeObserver that handles ALL dimension updates
 * - Clear separation: container CSS → chart init → canvas DOM attributes
 * - Eliminates timing issues and dimension mismatches
 */
/**
 * ✨ Crop canvas to remove white padding on LEFT only
 * 
 * Tìm content boundary từ trái, crop bỏ padding, GIỮ nguyên phần quyền + dưới
 * 
 * @param {HTMLCanvasElement} canvas - Original canvas
 * @param {number} targetWidth - Display width (for reference only)
 * @param {number} targetHeight - Display height (for reference only)
 * @returns {HTMLCanvasElement} Cropped canvas with left padding removed
 */
function cropCanvasContent(canvas, targetWidth = 900, targetHeight = 550) {
  try {
    const ctx = canvas.getContext('2d')
    if (!ctx) return canvas
    
    const width = canvas.width
    const height = canvas.height
    
    const imageData = ctx.getImageData(0, 0, width, height)
    const data = imageData.data
    
    // Find LEFT boundary - first non-white column
    let minX = width
    let foundContent = false
    
    // Scan every pixel to find leftmost content
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i]
      const g = data[i + 1]
      const b = data[i + 2]
      const a = data[i + 3]
      
      // Skip white/transparent pixels
      if (a === 0 || (r > 240 && g > 240 && b > 240)) {
        continue
      }
      
      foundContent = true
      const pixelIndex = i / 4
      const x = pixelIndex % width
      minX = Math.min(minX, x)
    }
    
    // If no content found, return original
    if (!foundContent) {
      console.log(`  No chart content detected`)
      return canvas
    }
    
    // Crop từ leftmost content đến hết canvas (không limit bởi target width)
    const paddingLeft = Math.max(0, minX - 5)  // Remove left padding + small margin
    const cropX = paddingLeft
    const cropY = 0
    
    // Take everything from crop point to RIGHT edge (full width)
    const cropW = width - cropX
    const cropH = height  // Take full height
    
    console.log(`  Detected content at x=${minX}, cropping from ${cropX} (${cropW}×${cropH} px)`)
    
    // Create cropped canvas
    const croppedCanvas = document.createElement('canvas')
    croppedCanvas.width = cropW
    croppedCanvas.height = cropH
    
    const croppedCtx = croppedCanvas.getContext('2d')
    croppedCtx.drawImage(canvas, cropX, cropY, cropW, cropH, 0, 0, cropW, cropH)
    
    return croppedCanvas
  } catch (error) {
    console.warn('⚠️  Canvas crop failed, returning original:', error)
    return canvas
  }
}

/**
 * ✨ NEW APPROACH: Image-Based Chart Rendering
 * Converts echarts canvas to image → displays image (no viewport dimension issues)
 * 
 * Why this works:
 * - Echarts renders once to canvas (works at any viewport)
 * - Convert canvas to PNG image data URL
 * - Display image in <img> tag (naturally responsive)
 * - No dimension sync issues, no viewport dependency
 */
function ChartRenderer({ content, metadata, questionCode = '', chartIndex = 0 }) {
  const [chartImageUrl, setChartImageUrl] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  
  // Parse metadata once
  const parsedMetadata = useMemo(() => {
    if (typeof metadata === 'string') {
      try {
        return JSON.parse(metadata)
      } catch (e) {
        console.error('Failed to parse metadata:', e)
        return null
      }
    }
    return metadata
  }, [metadata])

  // Memoize content to prevent unnecessary re-renders
  const memoizedContent = useMemo(() => {
    if (typeof content === 'string') {
      try {
        return JSON.parse(content)
      } catch {
        return content
      }
    }
    return content
  }, [content])

  // Get chart dimensions from metadata or use defaults
  const getChartSize = useCallback(() => {
    if (parsedMetadata?.width && parsedMetadata?.height) {
      const w = typeof parsedMetadata.width === 'number' ? parsedMetadata.width : parseInt(parsedMetadata.width)
      const h = typeof parsedMetadata.height === 'number' ? parsedMetadata.height : parseInt(parsedMetadata.height)
      return { width: w, height: h }
    }
    // ✨ Display size: 900×550px (smaller display)
    // But internal canvas will be 1000×600px to avoid truncation
    return { width: 900, height: 550 }
  }, [parsedMetadata])

  // Main effect: Create temporary container, render, convert to image, cleanup
  useEffect(() => {
    let timeoutId = null
    let chartInstance = null
    const tempDiv = document.createElement('div')

    const renderChart = async () => {
      try {
        setIsLoading(true)

        // 1️⃣ Parse chart options
        let options = memoizedContent?.echarts || memoizedContent
        if (!options || typeof options !== 'object') {
          console.warn('❌ No chart options found in content')
          setIsLoading(false)
          return
        }

        // 2️⃣ Resolve chart placeholders
        let resolvedOptions
        try {
          resolvedOptions = resolveChartOptionPlaceholders(options)
        } catch (resolveErr) {
          console.error('❌ Failed to resolve placeholders:', resolveErr)
          setIsLoading(false)
          return
        }

        // 3️⃣ Create temporary off-screen container and append to DOM
        const { width, height } = getChartSize()
        // ✨ Set container size (display size)
        tempDiv.style.cssText = `
          position: fixed;
          left: -9999px;
          top: -9999px;
          width: ${width}px;
          height: ${height}px;
          visibility: hidden;
          pointer-events: none;
          overflow: visible;
          z-index: -9999;
          margin: 0;
          padding: 0;
          border: none;
          box-sizing: border-box;
        `
        document.body.appendChild(tempDiv)
        
        // Force browser to layout the div
        await new Promise(resolve => setTimeout(resolve, 20))

        // 4️⃣ Initialize echarts in temporary div
        
        chartInstance = echarts.init(tempDiv, null, { 
          useDirtyRect: true,
          width: width, 
          height: height
        })
        
        // Set options FIRST
        chartInstance.setOption(resolvedOptions, true) // true = replace all options
        
        // CRITICAL: Resize echarts canvas to match the larger size
        chartInstance.resize({ width: width, height: height })
        
        // Wait for initial render
        await new Promise(resolve => setTimeout(resolve, 100))

        // 5️⃣ Wait for echarts to COMPLETE rendering
        // Complex charts (bar with many items, line with many points) need more time
        // 1500ms is safer than 1000ms for consistency, especially on first render
        await new Promise(resolve => setTimeout(resolve, 1500))

        // 6️⃣ Verify canvas exists and get dimensions before conversion
        const canvas = tempDiv.querySelector('canvas')
        if (!canvas) {
          console.warn('⚠️  Canvas not found after render')
          setIsLoading(false)
          return
        }
        
        const actualCanvasWidth = parseInt(canvas.getAttribute('width') || '0')
        const actualCanvasHeight = parseInt(canvas.getAttribute('height') || '0')
        console.log(`🎨 Canvas: ${actualCanvasWidth}×${actualCanvasHeight}px (CSS: ${canvas.style.width} × ${canvas.style.height})`)
        
        // 7️⃣ ✨ NEW: Crop canvas to remove white margins + trim to target size
        const croppedCanvas = cropCanvasContent(canvas, width, height)
        console.log(`✂️  Cropped canvas: ${croppedCanvas.width}×${croppedCanvas.height}px`)
        
        // 8️⃣ Convert canvas to PNG image
        const imageDataUrl = croppedCanvas.toDataURL('image/png', 1.0)
        console.log(
          `✅ [${questionCode || 'Q?'}] Chart converted to image (${Math.round(imageDataUrl.length / 1024)}KB)`
        )

        // 9️⃣ Display image
        setChartImageUrl(imageDataUrl)
        setIsLoading(false)
      } catch (error) {
        console.error('❌ Error rendering chart:', error)
        setIsLoading(false)
      }
    }

    // Wait for layout to settle, then render
    timeoutId = setTimeout(renderChart, 50)

    // Cleanup: Remove temporary div and dispose echarts instance
    return () => {
      if (timeoutId) clearTimeout(timeoutId)
      if (chartInstance) {
        chartInstance.dispose()
      }
      if (tempDiv.parentNode) {
        document.body.removeChild(tempDiv)
      }
    }
  }, [memoizedContent, questionCode, getChartSize])

  const { width: chartWidth, height: chartHeight } = getChartSize()

  // ✨ Create unique key for export identification
  const chartKey = `${questionCode || 'Q0'}-${chartIndex}`

  return (
    <div
      data-chart-ref={chartKey}
      data-question-code={questionCode || `Q${chartIndex}`}
      data-chart-index={String(chartIndex)}
      style={{
        width: typeof chartWidth === 'number' ? `${chartWidth}px` : chartWidth,
        height: typeof chartHeight === 'number' ? `${chartHeight}px` : chartHeight,
        margin: '0 auto',
        backgroundColor: '#ffffff',
        borderRadius: '4px',
        overflow: 'hidden',
        position: 'relative',
        padding: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      {isLoading && (
        <div style={{ textAlign: 'center', color: '#999', fontSize: '14px' }}>
          Đang tải biểu đồ...
        </div>
      )}

      {chartImageUrl && !isLoading && (
        <img
          src={chartImageUrl}
          alt={`Chart ${questionCode ? '[' + questionCode + ']' : ''}`}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            display: 'block'
          }}
        />
      )}
    </div>
  )
}

/**
 * ✨ Export chart canvas to Base64 PNG
 * Dùng để embed trực tiếp vào DOCX mà không cần re-render
 * @param {HTMLElement} chartRefElement - div chứa img
 * @returns {string|null} Base64 data URL hoặc null nếu error
 */
export function exportChartCanvasToBase64(chartRefElement) {
  try {
    if (!chartRefElement) {
      console.warn('❌ Chart ref element not found')
      return null
    }

    const img = chartRefElement.querySelector('img')
    if (!img) {
      console.warn('❌ Image element not found in chart ref')
      return null
    }

    // ✨ Get Base64 from img src (already data URL)
    return img.src
  } catch (e) {
    console.error('❌ Failed to export chart:', e)
    return null
  }
}

/**
 * ✨ Send chart image to server for DOCX export
 * @param {string} base64Image - Base64 PNG from canvas.toDataURL()
 * @param {string} chartTitle - Chart title for logging
 * @param {Object} questionMetadata - Metadata about the question (optional)
 * @returns {Promise<{success: boolean, imagePath?: string, error?: string}>}
 */
export async function sendChartImageToServer(base64Image, chartTitle = 'chart', questionMetadata = {}) {
  try {
    if (!base64Image) {
      console.warn('⚠️  No Base64 image provided')
      return { success: false, error: 'Empty image data' }
    }

    // Strip data URL prefix if present
    let imageData = base64Image
    if (imageData.startsWith('data:image')) {
      imageData = imageData.split(',')[1]
    }

    console.log(`📤 Uploading chart "${chartTitle}" (${Math.round(imageData.length / 1024)}KB)...`)

    const response = await fetch('/api/export/save-chart-image', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_base64: imageData,
        chart_title: chartTitle,
        metadata: questionMetadata,
        timestamp: new Date().toISOString()
      })
    })

    if (!response.ok) {
      const error = await response.text()
      console.error(`❌ Server error (${response.status}):`, error)
      return { success: false, error: `Server error: ${response.status}` }
    }

    const data = await response.json()
    if (data.success) {
      console.log(`✅ Chart uploaded: ${data.image_path}`)
      return { success: true, imagePath: data.image_path }
    } else {
      return { success: false, error: data.error || 'Unknown error' }
    }
  } catch (e) {
    console.error('❌ Failed to send chart to server:', e)
    return { success: false, error: e.message }
  }
}

/**
 * ✨ Direct download of chart as PNG (browser-only)
 * @param {HTMLElement} chartRefElement - div chứa img
 * @param {string} fileName - Download file name
 */
export function downloadChartAsImage(chartRefElement, fileName = 'chart.png') {
  try {
    const base64 = exportChartCanvasToBase64(chartRefElement)
    if (!base64) {
      console.error('❌ Failed to export chart')
      return
    }

    const link = document.createElement('a')
    link.href = base64
    link.download = fileName
    link.click()
    console.log(`✅ Chart downloaded as ${fileName}`)
  } catch (e) {
    console.error('❌ Failed to download chart:', e)
  }
}
