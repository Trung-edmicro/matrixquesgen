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
  console.log('📊 [ChartResolver] Input option:', option);

  // Deep clone để không modify original
  const resolved = JSON.parse(JSON.stringify(option));

  // Cache canvases để tái sử dụng
  const patternCache: { [key: string]: HTMLCanvasElement } = {};

  // Get yAxis max values - handle both single axis and array of axes (Combo charts)
  let yAxisMaxValue: number | undefined = undefined;
  if (resolved.yAxis) {
    if (Array.isArray(resolved.yAxis)) {
      // Combo/Multiple axes: use first axis (left) max as baseline
      yAxisMaxValue = resolved.yAxis[0]?.max;
      console.log('📊 [ChartResolver] Detected combo chart with yAxis array:', {
        yAxisCount: resolved.yAxis.length,
        leftAxisMax: resolved.yAxis[0]?.max,
        rightAxisMax: resolved.yAxis[1]?.max
      });
    } else {
      // Single axis
      yAxisMaxValue = resolved.yAxis.max;
      console.log('📊 [ChartResolver] Detected single axis chart, yAxisMax:', yAxisMaxValue);
    }
  }

  // Track replacements for debugging
  let replacementCount = 0;
  let patternCount = 0;

  /**
   * Recursive traversal và replacement
   */
  function traverse(obj: any, path: string[] = [], parentAxis: any = null): void {
    if (!obj || typeof obj !== 'object') return;

    // If we're inside a yAxis array, handle each axis separately
    if (Array.isArray(obj) && path[path.length - 1] === 'yAxis') {
      console.log('🔧 [ChartResolver] Detected yAxis array, traversing each axis separately:', {
        yAxisCount: obj.length,
        path: path.join('.')
      });
      for (let i = 0; i < obj.length; i++) {
        if (obj[i] && typeof obj[i] === 'object') {
          const axisName = i === 0 ? 'LEFT' : 'RIGHT';
          console.log(`🔧 [ChartResolver] Traversing ${axisName} axis [${i}] with max:`, obj[i].max);
          traverse(obj[i], [...path, i.toString()], obj[i]);
        }
      }
      return;
    }
    
    const currentAxisMax: number | undefined = parentAxis?.max || yAxisMaxValue;

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
        } else if (value === 'FORMATTER_PLACEHOLDER_LEFT') {
          // Left Y-axis formatter (Bar chart) - Hiển thị giá trị bên trái + tick marks
          // Ẩn mốc cao nhất (ngọn mũi tên)
          obj[key] = (val: number) => {
            // Nếu là mốc cao nhất, ẩn
            if (yAxisMaxValue && val > yAxisMaxValue - 1) {
              return '';
            }
            // Format number với dấu phân cách hàng nghìn
            const formatted = new Intl.NumberFormat('vi-VN').format(val);
            return `{value|${formatted}}{tick|}`;
          };
          replacementCount++;
        } else if (value === 'FORMATTER_PLACEHOLDER_RIGHT') {
          // Right Y-axis formatter (Line chart) - Hiển thị giá trị bên phải + tick marks
          // Ẩn mốc cao nhất và giá trị 0
          obj[key] = (val: number) => {
            // Ẩn nếu là mốc cao nhất hoặc bằng 0
            if (val === 0 || (yAxisMaxValue && val > yAxisMaxValue - 1)) {
              return '';
            }
            // Format number với dấu phân cách hàng nghìn
            const formatted = new Intl.NumberFormat('vi-VN').format(val);
            return `{tick|}{value|${formatted}}`;
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
        } else if (value === 'FORMATTER_Y_LEFT_PLACEHOLDER') {
          // Left Y-axis formatter (Combo chart bar) - Hiển thị giá trị bên trái + tick marks
          // Use currentAxisMax from left axis (index 0)
          const leftMax = currentAxisMax;
          console.log(`✓ Found FORMATTER_Y_LEFT_PLACEHOLDER at ${currentPath.join('.')}, leftMax:`, leftMax);
          obj[key] = (val: number) => {
            // Ẩn nếu là mốc cao nhất
            if (leftMax && val > leftMax - 1) {
              return '';
            }
            // Format number với dấu phân cách hàng nghìn
            const formatted = new Intl.NumberFormat('vi-VN').format(val);
            return `{value|${formatted}}{tick|}`;
          };
          replacementCount++;
        } else if (value === 'FORMATTER_Y_RIGHT_PLACEHOLDER') {
          // Right Y-axis formatter (Combo chart line) - Hiển thị giá trị bên phải + tick marks
          // Use currentAxisMax from right axis (index 1)
          const rightMax = currentAxisMax;
          console.log(`✓ Found FORMATTER_Y_RIGHT_PLACEHOLDER at ${currentPath.join('.')}, rightMax:`, rightMax);
          obj[key] = (val: number) => {
            // Ẩn nếu là mốc cao nhất hoặc bằng 0
            if (val === 0 || (rightMax && val > rightMax - 1)) {
              return '';
            }
            // Format number với dấu phân cách hàng nghìn
            const formatted = new Intl.NumberFormat('vi-VN').format(val);
            return `{tick|}{value|${formatted}}`;
          };
          replacementCount++;
        } else if (value === 'FORMATTER_LABEL_PLACEHOLDER_COMBO') {
          // Combo chart label formatter - format number với dấu phân cách
          obj[key] = (params: any) => {
            let val = params.value;
            if (typeof val === 'number') {
              return new Intl.NumberFormat('vi-VN').format(val);
            }
            return val?.toString() || '';
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
        // Keep parentAxis context when recursing to nested objects
        // This ensures nested formatters in axisLabel, tooltip, etc. know their axis context
        traverse(value, currentPath, parentAxis);
      }
    }
  }

  traverse(resolved, [], null);
  
  console.log(`🎨 [ChartResolver] Done! Replacements: ${replacementCount}, Patterns: ${patternCount}`);
  if (replacementCount === 0) {
    console.warn('⚠️ [ChartResolver] No placeholders were found! Check if option has placeholder strings.');
    console.log('📊 [ChartResolver] yAxis structure:', resolved.yAxis);
  }
  console.log('✓ Resolved option:', resolved);

  return resolved;
}
