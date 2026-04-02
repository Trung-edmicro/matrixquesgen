"""
Area Chart Generator for GenChart
Tạo biểu đồ miền (Area Chart) theo quy tắc lý thuyết vẽ biểu đồ
"""

import json
from services.utils.chart.utils import (
    validate_chart_data,
    get_pattern_styles,
    create_pattern_js_function
)

def generate_area_chart(data):
    """
    Tạo ECharts option cho biểu đồ miền (Area Chart)
    
    Quy tắc:
    - Trục X là mốc thời gian (boundaryGap: False).
    - Dữ liệu các series được cộng dồn (stack: 'Total').
    - Hiển thị nhãn giá trị nằm chính giữa các miền.
    - Nhãn ở cột đầu/cuối được dịch nhẹ để không bị cắt.
    
    Args:
        data: Dict chứa dữ liệu và tuỳ chọn
        
    Returns:
        dict: ECharts option
    """
    # Validate input
    is_valid, error_msg = validate_chart_data(data)
    if not is_valid:
        raise ValueError(f"Invalid data: {error_msg}")
    
    chart_data = data['data']
    user_options = data.get('options', {})
    
    categories = chart_data.get('categories', [])
    series_list = chart_data['series']
    
    # Tính toán khoảng cách (gap) giữa các năm nếu người dùng nhập số
    try:
        num_categories = [int(cat) for cat in categories]
        if sorted(num_categories) == num_categories and len(num_categories) > 1:
            diffs = [num_categories[i+1] - num_categories[i] for i in range(len(num_categories)-1)]
            min_diff = min(diffs)
            
            full_categories = []
            full_data_matrix = {i: [] for i in range(len(series_list))}
            
            for i in range(len(categories)):
                current_year = categories[i]
                full_categories.append(current_year)
                
                for s_idx, series in enumerate(series_list):
                    full_data_matrix[s_idx].append(series['data'][i])
                
                if i < len(categories) - 1:
                    gap = diffs[i]
                    empty_slots = max(0, int(round((gap / min_diff) - 1)))
                    
                    for _ in range(empty_slots):
                        full_categories.append(f"_{current_year}_{_}") 
                        for s_idx in range(len(series_list)):
                            full_data_matrix[s_idx].append('-')
            
            for s_idx, series in enumerate(series_list):
                series['data'] = full_data_matrix[s_idx]
                
            categories = full_categories
    except ValueError:
        pass # Giữ nguyên nếu không phải năm
    
    # Get pattern styles
    pattern_styles = get_pattern_styles()
    
    echarts_series = []
    label_scatter_data = []
    legend_data = []
    
    # 1. Build Area Series
    for idx, series in enumerate(series_list):
        pattern_type = pattern_styles[idx % len(pattern_styles)]['type']
        series_name = series.get('name', f'Series {idx + 1}')
        legend_data.append(series_name)
        
        series_config = {
            'name': series_name,
            'type': 'line',
            'stack': 'Total',
            'itemStyle': {
                'color': f'PATTERN_PLACEHOLDER_{pattern_type}', # Placeholder cho JS sau này, JS sẽ parse nếu có ngoặc kép
                'borderColor': '#000', # Thêm border cho legend và đường viền
                'borderWidth': 1
            },
            'areaStyle': {
                'color': f'PATTERN_PLACEHOLDER_{pattern_type}',
                'opacity': 1
            },
            'lineStyle': {
                'color': '#000',
                'width': 1.5
            },
            'showSymbol': False,
            'data': series['data'],
            '_patternType': pattern_type
        }
        echarts_series.append(series_config)
    
    # 2. Build Scatter Series for Labels (điểm giữa miền)
    show_labels = user_options.get('show_data_labels', True)
    if show_labels:
        for i in range(len(categories)):
            current_sum = 0
            for series in series_list:
                val = series['data'][i]
                if val is None:
                    continue
                    
                mid_y = current_sum + (val / 2)
                current_sum += val
                
                # Alignment config to prevent clipping on edges
                align_config = 'center'
                offset_config = [0, 0]
                
                if i == 0:
                    align_config = 'left'
                    offset_config = [5, 0]  # Đẩy nhẹ sang phải từ lề trái
                elif i == len(categories) - 1:
                    align_config = 'right'
                    offset_config = [-5, 0] # Đẩy nhẹ sang trái từ lề phải
                    
                label_scatter_data.append({
                    'value': [i, mid_y],
                    'realValue': val,
                    'label': {
                        'align': align_config,
                        'offset': offset_config
                    }
                })
        
        scatter_series = {
            'name': 'Labels',
            'type': 'scatter',
            'symbolSize': 0, # Tàng hình
            'z': 10, # Luôn nằm trên
            'data': label_scatter_data,
            'label': {
                'show': True,
                'position': 'inside',
                'formatter': 'FORMATTER_SCATTER_LABEL_PLACEHOLDER', # Sẽ chèn hàm JS vào đây
                'backgroundColor': '#fff',
                'borderColor': '#000',
                'borderWidth': 1.2,
                'padding': [4, 6],
                'color': '#000',
                'fontSize': 14,
                'fontWeight': 'bold',
                'borderRadius': 3
            },
            'tooltip': {
                'show': False
            },
            '_isLabelSeries': True
        }
        echarts_series.append(scatter_series)

    # 3. Build Axis & Global Options
    y_axis_unit = series_list[0].get('unit', '%') if series_list else '%'
    x_axis_unit = user_options.get('x_axis_unit', 'năm')
    
    option = {
        'textStyle': {
            'fontFamily': 'Roboto, sans-serif'
        },
        'title': {
            'text': user_options.get('title', ''),
            'subtext': user_options.get('subtitle', ''),
            'left': 'center',
            'bottom': '8%',
            'textStyle': {
                'fontSize': 16,
                'fontWeight': 'bold'
            },
            'subtextStyle': {
                'fontSize': 13,
                'fontStyle': 'italic'
            }
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'cross',
                'label': {
                    'backgroundColor': '#6a7985'
                }
            }
        },
        'legend': {
            'data': legend_data,
            'show': user_options.get('show_legend', True),
            'bottom': '18%', # Legend nằm cao nhất ở nhóm bottom
            'left': 'center',
            'icon': 'rect', # Buộc hiển thị hình chữ nhật để pattern hiển thị đẹp
            'itemWidth': 28,
            'itemHeight': 14,
            'itemGap': 20
        },
        'grid': {
            'left': 60,
            'right': 80, # Tăng margin để tránh text bị cắt
            'top': 40, # Kéo biểu đồ lên trên
            'bottom': 160, # Tăng khoảng trống dưới để chứa Legend, Title, Source
            'containLabel': True,
            'show': True,
            'borderColor': '#000',
            'borderWidth': 1.5
        },
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': categories,
            'name': x_axis_unit,
            'nameLocation': 'end',
            'nameGap': 15,
            'nameTextStyle': {
                'color': '#000',
                'fontSize': 13,
                'fontWeight': 'bold'
            },
            'axisLabel': {
                'color': '#000',
                'fontSize': 13,
                'margin': 12,
                'interval': 'FORMATTER_X_INTERVAL_PLACEHOLDER'
            },
            'axisLine': {
                'lineStyle': {
                    'color': '#000'
                }
            },
            'axisTick': {
                'show': True,
                'inside': False, # Chuyển tick ra ngoài
                'length': 5,
                'lineStyle': {
                    'color': '#000',
                    'width': 1.5
                }
            }
        },
        'yAxis': {
            'type': 'value',
            'name': y_axis_unit,
            'nameLocation': 'end',
            'nameGap': 20,
            'nameTextStyle': {
                'color': '#000',
                'fontSize': 13,
                'fontWeight': 'bold'
            },
            'axisLabel': {
                'color': '#000',
                'fontSize': 13
            },
            'axisLine': {
                'show': True,
                'lineStyle': {
                    'color': '#000'
                }
            },
            'axisTick': {
                'show': True,
                'inside': False, # Chuyển tick ra ngoài
                'length': 5,
                'lineStyle': {
                    'color': '#000',
                    'width': 1.5
                }
            },
            'splitLine': {
                'show': True,
                'lineStyle': {
                    'color': '#ddd'
                }
            },
            'min': 0,
            'max': 100 # Biểu đồ miền thường thể hiện % cơ cấu nên max mặc định là 100
        },
        'series': echarts_series
    }
    
    # Add source if provided
    if 'source' in user_options:
        option['graphic'] = [{
            'type': 'text',
            'left': 'center',
            'bottom': '2%',
            'style': {
                'text': user_options['source'],
                'fontSize': 12,
                'fontStyle': 'italic'
            }
        }]
    
    return option
