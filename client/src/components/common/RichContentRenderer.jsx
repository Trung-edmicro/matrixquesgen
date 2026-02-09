import { useMemo, useEffect, useRef } from 'react'
import LaTeXRenderer from './LaTeXRenderer'
import * as echarts from 'echarts'


/**
 * Component để render rich content (text, mixed với table/image/chart)
 * @param {Object} content - Content object với format {type: 'text'|'mixed', content: ...}
 * @param {boolean} contentEditable - Có cho phép chỉnh sửa không
 * @param {Function} onBlur - Callback khi blur (nếu contentEditable)
 * @param {string} className - Additional CSS classes
 */
export default function RichContentRenderer({ content, contentEditable = false, onBlur, className = '' }) {
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

  // Mixed content (text + tables + images + charts)
  if (type === 'mixed') {
    if (!Array.isArray(contentData)) {
      return <div className="text-red-500">Invalid mixed content format</div>
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

          if (typeof item === 'object') {
            // Table content
            if (item.type === 'table') {
              return <TableRenderer key={index} content={item.content} />
            }

            // Image content
            if (item.type === 'image') {
              return <ImageRenderer key={index} content={item.content} metadata={item.metadata} />
            }

            // Chart content (ECharts)
            if (item.type === 'chart') {
              return <ChartRenderer key={index} content={item.content} metadata={item.metadata} />
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
function TableRenderer({ content }) {
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

  return (
    <div className="overflow-x-auto my-3 flex justify-center">
      <table className="border-collapse border border-gray-300 text-sm table-auto">
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
    </div>
  )
}

/**
 * Component để render image (local hoặc URL)
 */
function ImageRenderer({ content, metadata }) {
  const imageUrl = typeof content === 'string' ? content : content?.url || content?.content

  return (
    <div className="my-3">
      <img
        src={imageUrl}
        alt={metadata?.[0] || 'Question image'}
        className="max-w-full h-auto rounded border border-gray-200"
        onError={(e) => {
          e.target.style.display = 'none'
          e.target.parentElement.innerHTML = `<div class="text-red-500 text-sm">Failed to load image: ${imageUrl}</div>`
        }}
      />
      {metadata && Array.isArray(metadata) && metadata.length > 0 && (
        <div className="text-sm text-gray-600 mt-2">
          {metadata.map((meta, idx) => (
            <div key={idx}>
              <LaTeXRenderer>{meta}</LaTeXRenderer>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Component để render ECharts chart
 */
function ChartRenderer({ content, metadata }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

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

      // Initialize or update chart
      if (!chartInstance.current) {
        chartInstance.current = echarts.init(chartRef.current)
      }

      chartInstance.current.setOption(options)

      // Cleanup on unmount
      return () => {
        if (chartInstance.current) {
          chartInstance.current.dispose()
          chartInstance.current = null
        }
      }
    } catch (e) {
      console.error('Failed to render chart:', e, content)
    }
  }, [content])

  // Parse metadata if it's a string
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

  return (
    <div className="my-3 flex flex-col items-center">
      <div ref={chartRef} style={{ width: '100%', maxWidth: '800px', height: '400px' }} />
      {/* {parsedMetadata?.caption && (
        <div className="text-sm text-gray-600 mt-2 text-center italic">
          <LaTeXRenderer>{parsedMetadata.caption}</LaTeXRenderer>
        </div>
      )} */}
      {/* {parsedMetadata?.source && (
        <div className="text-xs text-gray-500 mt-1 text-center">
          <LaTeXRenderer>{parsedMetadata.source}</LaTeXRenderer>
        </div>
      )} */}
    </div>
  )
}
