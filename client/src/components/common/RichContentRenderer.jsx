import { useMemo, useEffect, useRef, useState } from 'react'
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
 * Component để render ECharts chart
 */
function ChartRenderer({ content, metadata, questionCode = '', chartIndex = 0 }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)
  const containerRef = useRef(null)

  // Parse metadata if it's a string - MUST BE FIRST
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

  // Responsive sizing hook - use metadata from backend if provided
  const [dimensions, setDimensions] = useState({ width: '100%', maxWidth: '850px', height: '500px' })

  useEffect(() => {
    const updateDimensions = () => {
      if (!containerRef.current) return

      const screenWidth = window.innerWidth
      let calculatedMaxWidth = '850px'
      let calculatedHeight = '500px'

      // Responsive sizing based on viewport
      // Allow backend metadata to override (for pie charts with square dimensions)
      if (parsedMetadata?.width && parsedMetadata?.height) {
        // Use exact backend dimensions (converted to px if number)
        const metaWidth = typeof parsedMetadata.width === 'number' ? parsedMetadata.width : parseInt(parsedMetadata.width)
        const metaHeight = typeof parsedMetadata.height === 'number' ? parsedMetadata.height : parseInt(parsedMetadata.height)
        
        // Detect pie chart (square dimensions from backend: 550x550)
        const isPie = Math.abs(metaWidth - metaHeight) < 50 && Math.abs(metaWidth - 550) < 50
        
        if (isPie) {
          // Pie chart: never responsive, always 550x550
          calculatedMaxWidth = '550px'
          calculatedHeight = '550px'
        } else {
          // Bar/Line/Area: use backend dimensions
          calculatedMaxWidth = `${metaWidth}px`
          calculatedHeight = `${metaHeight}px`
        }
      } else {
        // Fallback: responsive based on viewport for bar/line charts
        // Aspect ratio: 1.7:1 (width:height) - compact, balanced
        if (screenWidth < 640) {
          // Mobile: full width, proportional height
          calculatedMaxWidth = '100%'
          calculatedHeight = '300px'
        } else if (screenWidth < 1024) {
          // Tablet: proportional scaling
          calculatedMaxWidth = '95%'
          calculatedHeight = '450px'
        } else if (screenWidth < 1280) {
          // Small desktop
          calculatedMaxWidth = '820px'
          calculatedHeight = '480px'
        } else {
          // Large desktop: full 850x500
          calculatedMaxWidth = '850px'
          calculatedHeight = '500px'
        }
      }

      setDimensions({
        width: '100%',
        maxWidth: calculatedMaxWidth,
        height: calculatedHeight,
      })
    }

    updateDimensions()
    const resizeListener = () => updateDimensions()
    window.addEventListener('resize', resizeListener)
    return () => window.removeEventListener('resize', resizeListener)
  }, [parsedMetadata])

  useEffect(() => {
    if (!chartRef.current) return

    try {
      // Parse chart data
      let chartData
      if (typeof content === 'string') {
        chartData = JSON.parse(content)
      } else {
        chartData = content
      }

      // Extract ECharts options from nested structure
      // Expected format: {chartType: "bar", echarts: {...}} or just {...}
      let options
      if (chartData.echarts) {
        options = chartData.echarts
      } else if (chartData.chartType) {
        // Legacy format - ignore
        console.warn('Chart data has chartType but no echarts config')
        return
      } else {
        // Direct ECharts options
        options = chartData
      }

      // ✨ RESOLVE PLACEHOLDERS: Convert string placeholders to actual functions
      const resolvedOptions = resolveChartOptionPlaceholders(options)

      // Initialize or update chart
      if (!chartInstance.current) {
        chartInstance.current = echarts.init(chartRef.current)
      }

      chartInstance.current.setOption(resolvedOptions)

      // ✨ KEY FIX: Increase canvas DOM width to prevent content cutoff
      // For pie charts: use exact square (550×550)
      // For bar/line charts: use 50px buffer for content breathing room
      try {
        const canvas = chartRef.current?.querySelector('canvas')
        if (canvas) {
          // Get dimensions - parse CSS width/height to numbers
          let cssWidth = 850  // Default
          let cssHeight = 500  // Default
          
          // Try to get from offset first
          const offsetWidth = chartRef.current?.offsetWidth
          const offsetHeight = chartRef.current?.offsetHeight
          
          if (offsetWidth && offsetWidth > 0) {
            cssWidth = offsetWidth
          } else if (dimensions.maxWidth) {
            // Fallback: parse from dimensions string
            const widthStr = String(dimensions.maxWidth)
            const parsed = parseInt(widthStr)
            if (!isNaN(parsed) && parsed > 0) {
              cssWidth = parsed
            }
          }
          
          if (offsetHeight && offsetHeight > 0) {
            cssHeight = offsetHeight
          } else if (dimensions.height) {
            // Fallback: parse from dimensions string
            const heightStr = String(dimensions.height)
            const parsed = parseInt(heightStr)
            if (!isNaN(parsed) && parsed > 0) {
              cssHeight = parsed
            }
          }
          
          // Detect if pie chart (square aspect ratio - width ≈ height)
          const isPieChart = Math.abs(cssWidth - cssHeight) < 50
          
          let domWidth, domHeight
          if (isPieChart) {
            // Pie chart: keep square to avoid distortion (550×550 exact)
            domWidth = cssWidth
            domHeight = cssHeight
          } else {
            // ✨ FIX: Scale buffer dynamically based on width
            // Formula: max(50px, 5% of width) to handle very long charts
            // This ensures labels and legend have enough space regardless of chart width
            const dynamicBuffer = Math.max(50, Math.round(cssWidth * 0.05))
            domWidth = cssWidth + dynamicBuffer
            domHeight = cssHeight
          }
          
          // Ensure values are positive integers
          domWidth = Math.max(50, Math.floor(domWidth))
          domHeight = Math.max(50, Math.floor(domHeight))
          
          // Set canvas DOM attributes (must be set, not CSS)
          canvas.setAttribute('width', domWidth.toString())
          canvas.setAttribute('height', domHeight.toString())
          
          // Force re-render after attribute change
          chartInstance.current.resize()
        }
      } catch (e) {
        console.error('Error adjusting canvas dimensions:', e)
        // Silently fail - chart will still render with default echarts sizing
      }

      // Handle resize
      const handleResize = () => {
        if (chartInstance.current) {
          chartInstance.current.resize()
        }
      }
      window.addEventListener('resize', handleResize)

      // Cleanup on unmount
      return () => {
        window.removeEventListener('resize', handleResize)
        if (chartInstance.current) {
          chartInstance.current.dispose()
          chartInstance.current = null
        }
      }
    } catch (e) {
      console.error('Failed to render chart:', e, content)
    }
  }, [content, dimensions])

  return (
    <div 
      ref={containerRef}
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        margin: 0,
        padding: 0
      }}
    >
      <div
        ref={chartRef}
        // ✨ NEW: Set data attributes for export identification
        data-chart-ref={questionCode ? `${questionCode}-${chartIndex}` : `chart-${chartIndex}`}
        data-question-code={questionCode || `Q${chartIndex}`}
        data-chart-index={String(chartIndex)}
        style={{
          position: 'relative',
          width: dimensions.maxWidth,
          height: dimensions.height,
          padding: '0px',
          margin: '0px',
          borderWidth: '0px',
          cursor: 'default',
          flexShrink: 0
        }}
      />
    </div>
  )
}

/**
 * ✨ Export chart canvas to Base64 PNG
 * Dùng để embed trực tiếp vào DOCX mà không cần re-render
 * @param {HTMLElement} chartRefElement - div chứa canvas
 * @returns {string|null} Base64 data URL hoặc null nếu error
 */
export function exportChartCanvasToBase64(chartRefElement) {
  try {
    if (!chartRefElement) {
      console.warn('❌ Chart ref element not found')
      return null
    }

    const canvas = chartRefElement.querySelector('canvas')
    if (!canvas) {
      console.warn('❌ Canvas element not found in chart ref')
      return null
    }

    // ✨ Convert canvas to PNG (quality 100%)
    const dataUrl = canvas.toDataURL('image/png', 1.0)
    return dataUrl
  } catch (e) {
    console.error('❌ Failed to export chart canvas:', e)
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
 * @param {HTMLElement} chartRefElement - div chứa canvas
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
