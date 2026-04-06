/**
 * Chart Export Service
 * Handles canvas-to-Base64 conversion and sending chart images to server for DOCX export
 * 
 * This service provides the bridge between client-rendered charts and server-side DOCX generation,
 * eliminating the need for Playwright-based rendering (3-5s per chart) in favor of direct
 * Base64 canvas export (~100ms per chart).
 */

/**
 * Export all chart images in the document as Base64 PNG
 * 
 * ✨ NEW FLOW: Extracts Base64 image directly from <img> tag (not canvas)
 * - ChartRenderer now renders chart as <img src="data:image/png;base64,...">
 * - Canvas is temporary (created in hidden div, then removed)
 * - This function extracts the Base64 from the img src attribute
 * 
 * @returns {Promise<Object>} Dictionary mapping "question_code-chart_index" to Base64 strings
 * 
 * Example output:
 * {
 *   "C1-0": "iVBORw0KGgo...",
 *   "C1-1": "iVBORw0KGgo...",
 *   "C2-0": "iVBORw0KGgo..."
 * }
 */
export async function captureAllChartImages() {
  const chartImages = {};
  
  try {
    // Find all chart containers marked with data-chart-ref
    const chartContainers = document.querySelectorAll('[data-chart-ref]');
    
    if (chartContainers.length === 0) {
      console.warn('⚠️  No chart containers found with [data-chart-ref]');
      return chartImages;
    }
        
    // Process each chart
    let totalSize = 0;
    chartContainers.forEach((container, index) => {
      try {
        // ✨ NEW: Try to get image from <img> tag first (image-based rendering)
        let base64 = null;
        const imgTag = container.querySelector('img');
        
        if (imgTag && imgTag.src && imgTag.src.startsWith('data:image/png')) {
          // Extract Base64 from img src attribute
          const dataUrl = imgTag.src;
          
          // Split on comma to get the Base64 part
          if (dataUrl.includes(',')) {
            base64 = dataUrl.split(',')[1];
          } else {
            console.warn(`⚠️  Invalid data URL format in chart ${index}`);
            return;
          }
          
          console.log(`✅ [Chart ${index}] Extracted from <img> tag`);
        } else {
          // Fallback: Try canvas (for compatibility with old rendering method)
          const canvas = container.querySelector('canvas');
          if (canvas) {
            const dataUrl = canvas.toDataURL('image/png', 1.0);
            base64 = dataUrl.split(',')[1];
            console.log(`⚠️  [Chart ${index}] Extracted from canvas (old method)`);
          }
        }
        
        if (!base64) {
          console.warn(`⚠️  No image data found in chart container ${index} (missing img or canvas)`);
          return;
        }
        
        // Get chart metadata from container attributes
        const questionCode = container.getAttribute('data-question-code') || `Q${index}`;
        const chartIndex = parseInt(container.getAttribute('data-chart-index') || index);
        
        // Create key for this chart
        const key = `${questionCode}-${chartIndex}`;
        chartImages[key] = base64;
        totalSize += base64.length / 1024;
        
        console.log(`  📊 [${key}] Captured (${Math.round(base64.length / 1024)}KB)`);
        
      } catch (error) {
        console.error(`  ✗ Error processing chart ${index}:`, error);
      }
    });
    
    console.log(`✅ [Export] Captured ${Object.keys(chartImages).length} charts (${Math.round(totalSize)}KB total)`);
    return chartImages;
    
  } catch (error) {
    console.error('❌ Error capturing chart images:', error);
    return chartImages;
  }
}

/**
 * Export single chart from a specific container
 * 
 * @param {HTMLElement} container - The chart container element
 * @param {string} questionCode - Question code for indexing (e.g., "C1")
 * @param {number} chartIndex - Chart index within the question (default: 0)
 * @returns {Promise<string>} Base64 PNG string or null if error
 */
export async function captureChartImage(container, questionCode, chartIndex = 0) {
  try {
    if (!container) {
      console.error('Container element not provided');
      return null;
    }
    
    const canvas = container.querySelector('canvas');
    if (!canvas) {
      console.warn('No canvas element found in container');
      return null;
    }
    
    const base64 = canvas.toDataURL('image/png', 1.0);
    return base64;
    
  } catch (error) {
    console.error(`Error capturing chart image for ${questionCode}-${chartIndex}:`, error);
    return null;
  }
}

/**
 * Export document with chart images included
 * 
 * This function:
 * 1. Captures all chart canvases as Base64 PNG
 * 2. Sends them to the server API along with export request
 * 3. Server embeds images directly in DOCX (no Playwright rendering needed)
 * 
 * @param {string} sessionId - Session ID for export endpoint
 * @param {string} apiBaseUrl - Base URL for API (default: auto-detect)
 * @returns {Promise<Object>} Export response with file path and download URL
 * 
 * @example
 * const result = await exportDocumentWithCharts('my-session-123');
 * if (result.success) {
 *   window.location.href = result.download_url;  // Download file
 * }
 */
export async function exportDocumentWithCharts(sessionId, apiBaseUrl = null) {
  try {
    // Auto-detect API base URL if not provided
    if (!apiBaseUrl) {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      const port = window.location.port ? `:${window.location.port}` : '';
      apiBaseUrl = `${protocol}//${hostname}${port}`;
    }
    
    
    // Step 1: Capture all chart images
    const chartImages = await captureAllChartImages();
    const chartCount = Object.keys(chartImages).length;
    
    // Step 2: Send export request with chart images
    const exportUrl = `${apiBaseUrl}/api/export/${sessionId}`;
    const response = await fetch(exportUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chart_images: chartImages
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Export failed (${response.status}): ${errorText}`);
    }
    
    const result = await response.json();
    
    return {
      success: true,
      file_name: result.file_name,
      file_path: result.file_path,
      download_url: `${apiBaseUrl}${result.download_url}`,
      chart_count: chartCount
    };
    
  } catch (error) {
    console.error('Export error:', error);
    return {
      success: false,
      error: error.message,
      chart_count: Object.keys(await captureAllChartImages()).length
    };
  }
}

/**
 * Setup data attributes on chart containers for proper identification
 * 
 * This should be called when rendering questions with charts.
 * It ensures each chart container has the necessary data attributes for export.
 * 
 * @param {HTMLElement} questionElement - The question container element
 * @param {string} questionCode - Question code (e.g., "C1", "C2")
 * @example
 * setupChartAttributes(questionDiv, 'C1');
 */
export function setupChartAttributes(questionElement, questionCode) {
  if (!questionElement) return;
  
  // Find all chart containers in this question
  const charts = questionElement.querySelectorAll('.chart-container, [role="img"][data-echarts]');
  
  charts.forEach((chartContainer, index) => {
    // Ensure it has data-chart-ref attribute
    if (!chartContainer.hasAttribute('data-chart-ref')) {
      chartContainer.setAttribute('data-chart-ref', `${questionCode}-chart-${index}`);
    }
    
    // Set question code and chart index
    if (!chartContainer.hasAttribute('data-question-code')) {
      chartContainer.setAttribute('data-question-code', questionCode);
    }
    
    if (!chartContainer.hasAttribute('data-chart-index')) {
      chartContainer.setAttribute('data-chart-index', String(index));
    }
  });
}

/**
 * Download individual chart as PNG without going to server
 * Useful for users who want to export charts separately
 * 
 * @param {HTMLElement} container - Chart container element
 * @param {string} filename - Download filename (default: "chart.png")
 */
export function downloadChartAsImage(container, filename = 'chart.png') {
  try {
    const canvas = container.querySelector('canvas');
    if (!canvas) {
      console.error('No canvas found in container');
      return;
    }
    
    // Convert canvas to blob and download
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
    }, 'image/png', 1.0);
  } catch (error) {
    console.error('Error downloading chart:', error);
  }
}

/**
 * Get export statistics without actually exporting
 * Useful for debugging and performance monitoring
 * 
 * @returns {Promise<Object>} Statistics about charts ready for export
 */
export async function getExportStatistics() {
  try {
    const chartImages = await captureAllChartImages();
    const chartCount = Object.keys(chartImages).length;
    let totalSize = 0;
    let largestChart = { key: null, size: 0 };
    
    Object.entries(chartImages).forEach(([key, base64]) => {
      const sizeKB = base64.length / 1024;
      totalSize += sizeKB;
      
      if (sizeKB > largestChart.size) {
        largestChart = { key, size: sizeKB };
      }
    });
    
    return {
      chart_count: chartCount,
      total_size_kb: totalSize,
      total_size_mb: (totalSize / 1024).toFixed(2),
      average_size_kb: chartCount > 0 ? (totalSize / chartCount).toFixed(1) : 0,
      largest_chart: largestChart,
      estimated_export_time_ms: chartCount * 100 + 500  // ~100ms per chart + 500ms overhead
    };
  } catch (error) {
    console.error('Error getting export statistics:', error);
    return null;
  }
}

export default {
  captureAllChartImages,
  captureChartImage,
  exportDocumentWithCharts,
  setupChartAttributes,
  downloadChartAsImage,
  getExportStatistics
};
