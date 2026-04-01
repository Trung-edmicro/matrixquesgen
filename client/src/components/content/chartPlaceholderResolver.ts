/**
 * Chart Placeholder Resolver
 * Chuyển đổi string placeholders từ backend thành functions/patterns thực tế
 * Áp dụng cho formatter, patterns, intervals, v.v.
 */

/**
 * Tạo canvas pattern (trả về canvas, không phải CanvasPattern)
 * Canvas sẽ được wrap trong pattern config object cho echarts
 */
function createPatternCanvas(type: string): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  canvas.width = 16;
  canvas.height = 16;

  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, 16, 16);
  ctx.strokeStyle = '#000';
  ctx.fillStyle = '#000';
  ctx.lineWidth = 1;

  if (type === 'dots') {
    // Chấm bi
    ctx.beginPath();
    ctx.arc(4, 4, 1.5, 0, Math.PI * 2);
    ctx.arc(12, 12, 1.5, 0, Math.PI * 2);
    ctx.fill();
  } else if (type === 'diagonal') {
    // Sọc chéo
    ctx.beginPath();
    ctx.moveTo(0, 16);
    ctx.lineTo(16, 0);
    ctx.moveTo(-8, 8);
    ctx.lineTo(8, -8);
    ctx.moveTo(8, 24);
    ctx.lineTo(24, 8);
    ctx.stroke();
  } else if (type === 'zigzag') {
    // Gợn sóng/Zigzag
    ctx.beginPath();
    ctx.moveTo(0, 4);
    ctx.lineTo(4, 0);
    ctx.lineTo(8, 4);
    ctx.lineTo(12, 0);
    ctx.lineTo(16, 4);
    ctx.moveTo(0, 12);
    ctx.lineTo(4, 8);
    ctx.lineTo(8, 12);
    ctx.lineTo(12, 8);
    ctx.lineTo(16, 12);
    ctx.stroke();
  } else if (type === 'cross') {
    // Caro
    ctx.fillStyle = '#ddd';
    ctx.fillRect(0, 0, 16, 16);
    ctx.strokeStyle = '#000';
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(16, 16);
    ctx.moveTo(16, 0);
    ctx.lineTo(0, 16);
    ctx.stroke();
  } else if (type === 'horizontal') {
    // Kẻ ngang
    ctx.beginPath();
    ctx.moveTo(0, 4);
    ctx.lineTo(16, 4);
    ctx.moveTo(0, 12);
    ctx.lineTo(16, 12);
    ctx.stroke();
  } else if (type === 'vertical') {
    // Kẻ dọc
    ctx.beginPath();
    ctx.moveTo(4, 0);
    ctx.lineTo(4, 16);
    ctx.moveTo(12, 0);
    ctx.lineTo(12, 16);
    ctx.stroke();
  } else if (type === 'grid') {
    // Lưới
    ctx.beginPath();
    ctx.moveTo(0, 8);
    ctx.lineTo(16, 8);
    ctx.moveTo(8, 0);
    ctx.lineTo(8, 16);
    ctx.stroke();
  } else if (type === 'diagonal_reverse') {
    // Sọc chéo ngược
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(16, 16);
    ctx.moveTo(-8, 8);
    ctx.lineTo(8, 24);
    ctx.moveTo(8, -8);
    ctx.lineTo(24, 8);
    ctx.stroke();
  }

  return canvas;
}

/**
 * Resolve echarts option - chuyển string placeholders thành functions/patterns
 */
export function resolveChartPlaceholders(option: any): any {
  if (!option || typeof option !== 'object') {
    return option;
  }

  console.log('🔧 [ChartResolver] Starting placeholder resolution...');

  // Deep clone để không modify original
  const resolved = JSON.parse(JSON.stringify(option));

  // Cache canvases để tái sử dụng
  const patternCache: { [key: string]: HTMLCanvasElement } = {};

  // Get yAxis max value for formatter
  const yAxisMaxValue = resolved.yAxis?.max;

  // Track replacements for debugging
  let replacementCount = 0;
  let patternCount = 0;

  /**
   * Recursive traversal và replacement
   */
  function traverse(obj: any, path: string[] = []): void {
    if (!obj || typeof obj !== 'object') return;

    for (const key in obj) {
      if (!obj.hasOwnProperty(key)) continue;

      const value = obj[key];
      const currentPath = [...path, key];

      // String placeholders - replace with functions
      if (typeof value === 'string') {
        if (value === 'FORMATTER_PLACEHOLDER') {
          // Y-axis formatter: Hiển thị giá trị số nguyên + rich text tick marks
          // Ẩn mốc cao nhất (ngọn mũi tên)
          obj[key] = (val: number) => {
            // Nếu là mốc cao nhất, ẩn
            if (yAxisMaxValue && val > yAxisMaxValue - 1) {
              return '';
            }
            // Trả về số liệu + rich text tick mark
            return `{value|${val}}{tick|}`;
          };
          replacementCount++;
        } else if (value === 'FORMATTER_LABEL_PLACEHOLDER_BAR') {
          // Bar chart label formatter - format number với K/M
          obj[key] = (params: any) => {
            let val = params.value;
            if (typeof val === 'number') {
              if (val > 1000000) return (val / 1000000).toFixed(1) + 'M';
              if (val > 1000) return (val / 1000).toFixed(1) + 'K';
            }
            return val?.toString() || '';
          };
          replacementCount++;
        } else if (value === 'FORMATTER_LABEL_PLACEHOLDER_PIE') {
          // Pie chart label formatter
          obj[key] = (params: any) => {
            if (params.value !== null && params.value !== undefined) {
              return params.value.toString();
            }
            return '';
          };
          replacementCount++;
        } else if (value === 'FORMATTER_LABEL_PLACEHOLDER') {
          // Line/Area chart label formatter
          obj[key] = (params: any) => {
            let val = params.value;
            if (typeof val === 'number') {
              if (val > 1000000) return (val / 1000000).toFixed(1) + 'M';
              if (val > 1000) return (val / 1000).toFixed(1) + 'K';
            }
            return val?.toString() || '';
          };
          replacementCount++;
        } else if (value === 'FORMATTER_SCATTER_LABEL_PLACEHOLDER') {
          // Scatter/Area scatter label
          obj[key] = (params: any) => {
            if (Array.isArray(params)) {
              return params[1]?.toString() || '';
            }
            return '';
          };
          replacementCount++;
        } else if (value === 'FORMATTER_X_PLACEHOLDER') {
          // X-axis formatter
          obj[key] = (value: any) => {
            return value.toString();
          };
          replacementCount++;
        } else if (value === 'FORMATTER_X_INTERVAL_PLACEHOLDER') {
          // X-axis interval - hiển thị tất cả labels
          obj[key] = (index: number) => {
            return 0; // interval = 0 = show all labels
          };
          replacementCount++;
        }
        // Pattern placeholders - replace with pattern config objects
        else if (value.startsWith('PATTERN_PLACEHOLDER_')) {
          const patternType = value.replace('PATTERN_PLACEHOLDER_', '');
          if (!patternCache[patternType]) {
            patternCache[patternType] = createPatternCanvas(patternType);
          }
          // Wrap canvas trong pattern config object như demo
          obj[key] = {
            type: 'pattern',
            image: patternCache[patternType],
            repeat: 'repeat'
          };
          patternCount++;
          replacementCount++;
        }
      }
      // Handle _patternType meta field - apply to itemStyle
      else if (key === '_patternType' && typeof value === 'string') {
        // Tạo itemStyle nếu chưa có
        if (!obj.itemStyle) {
          obj.itemStyle = {};
        }
        // Apply pattern config object
        if (!patternCache[value]) {
          patternCache[value] = createPatternCanvas(value);
        }
        obj.itemStyle.color = {
          type: 'pattern',
          image: patternCache[value],
          repeat: 'repeat'
        };
        console.log(`  ✓ Applied pattern "${value}" to series at path: ${currentPath.join('.')}`);
        patternCount++;
        delete obj[key]; // Xóa meta field
      }
      // Recursively traverse nested objects and arrays
      else if (typeof value === 'object' && value !== null) {
        traverse(value, currentPath);
      }
    }
  }

  traverse(resolved);
  
  console.log(`🎨 [ChartResolver] Done! Replacements: ${replacementCount}, Patterns: ${patternCount}`);
  console.log('✓ Resolved option:', resolved);

  return resolved;
}
