"""
Line Chart Generator for GenChart
Tạo biểu đồ đường (Line Chart) theo quy tắc lý thuyết vẽ biểu đồ
"""

from services.utils.chart.utils import (
    find_min_max,
    get_pattern_styles,
    calculate_axis_interval,
    validate_chart_data,
    merge_options,
    create_pattern_js_function
)


def generate_line_chart(data):
    """
    Tạo ECharts option cho biểu đồ đường
    
    Quy tắc theo lý thuyết:
    - Tỉ lệ: chiều cao trục tung = 2/3 chiều dài trục hoành
    - Năm đầu tiên gắn liền với trục tung (boundaryGap = false)
    - Nối các điểm bằng đoạn thẳng (smooth = false)
    - Hiển thị số liệu tại các điểm
    - Đánh số chuẩn trên trục tung cách đều
    - Đơn vị rõ ràng cho cả 2 trục
    - Hỗ trợ nhiều đường với màu sắc khác nhau
    
    Args:
        data: Dict với format:
        {
            "chart_type": "line",
            "data": {
                "categories": ["2020", "2021", "2022"],  # Trục X
                "series": [
                    {
                        "name": "GDP",
                        "data": [100, 120, 150],
                        "unit": "tỷ USD"
                    }
                ]
            },
            "options": {  # Optional
                "title": "Biểu đồ tăng trưởng GDP",
                "subtitle": "Giai đoạn 2020-2022",
                "show_legend": True,
                "show_data_labels": True,
                "smooth": False  # True nếu muốn đường cong
            }
        }
    
    Returns:
        dict: ECharts option
    """
    # Validate input
    is_valid, error_msg = validate_chart_data(data)
    if not is_valid:
        raise ValueError(f"Invalid data: {error_msg}")
    
    chart_data = data['data']
    user_options = data.get('options', {})
    
    # Extract data
    categories = chart_data.get('categories', [])
    series_list = chart_data['series']
    
    # Find min/max for scaling
    all_values = [s['data'] for s in series_list]
    min_val, max_val = find_min_max(all_values)
    
    # Calculate axis
    axis_min, axis_max, interval = calculate_axis_interval(min_val, max_val)
    
    # Extend max for arrow
    axis_max_extended = axis_max + interval
    axis_max_display = axis_max
    
    # Get pattern styles
    pattern_styles = get_pattern_styles()
    
    # Symbol styles cho các đường khác nhau
    symbols = ['circle', 'rect', 'triangle', 'diamond', 'pin', 'arrow']
    
    # Build series
    echarts_series = []
    show_labels = user_options.get('show_data_labels', True)
    is_smooth = user_options.get('smooth', False)
    
    for idx, series in enumerate(series_list):
        pattern_type = pattern_styles[idx % len(pattern_styles)]['type']
        
        series_config = {
            'name': series.get('name', f'Series {idx + 1}'),
            'type': 'line',
            'data': series['data'],
            'smooth': is_smooth,
            'symbol': symbols[idx % len(symbols)],
            'symbolSize': 8,
            'label': {
                'show': show_labels,
                'position': 'top',
                'formatter': 'FORMATTER_LABEL_PLACEHOLDER', # Sẽ chèn hàm JS vào đây
                'fontSize': 11,
                'color': '#000'
            },
            'lineStyle': {
                'width': 2,
                'color': '#000'
            },
            'itemStyle': {
                'color': '#fff',
                'borderColor': '#000',
                'borderWidth': 2
            },
            '_patternType': pattern_type
        }
        
        echarts_series.append(series_config)
    
    # Build legend
    legend_data = [s.get('name', f'Series {i+1}') for i, s in enumerate(series_list)]
    
    # Get unit from first series
    y_axis_unit = series_list[0].get('unit', '') if series_list else ''
    x_axis_unit = user_options.get('x_axis_unit', 'năm')
    
    # Build chart option
    option = {
        'textStyle': {
            'fontFamily': 'Roboto, sans-serif'
        },
        'title': {
            'text': user_options.get('title', ''),
            'subtext': user_options.get('subtitle', ''),
            'left': 'center',
            'bottom': '8%', # Đặt title ở dưới biểu đồ, trên source
            'textStyle': {
                'fontSize': 16,
                'fontWeight': 'bold'
            }
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'line'
            }
        },
        'legend': {
            'data': legend_data,
            'show': user_options.get('show_legend', True) and len(series_list) > 1,
            'bottom': '18%', # Legend nằm cao hơn title
            'left': 'center'
        },
        'grid': {
            'left': 80,
            'right': 80, # Tăng margin để tránh text bị cắt
            'top': 40, # Giảm top margin vì title đã chuyển xuống dưới
            'bottom': 160, # Tăng bottom margin để chứa legend, title, source
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': categories,
            'max': len(categories), # Mở rộng trục hoành thêm 1 khoảng mốc (bằng khoảng cách giữa 2 mốc)
            'name': x_axis_unit,
            'nameLocation': 'end',
            'nameGap': 12,
            'nameTextStyle': {
                'fontSize': 13
            },
            'axisLine': {
                'show': True,
                'symbol': ['none', 'arrow'], # Mũi tên chuẩn, không bị dẹt
                'symbolSize': [8, 12],
                'lineStyle': {
                    'color': '#000'
                }
            },
            'axisTick': {
                'show': False # Tắt tick mặc định
            },
            'axisLabel': {
                'color': '#000',
                'fontSize': 12,
                'formatter': 'FORMATTER_X_PLACEHOLDER', # Thay bằng JS
                'margin': 0, # Sát vào trục
                'padding': 0,
                'verticalAlign': 'top',
                'align': 'center',
                'rich': {
                    'value': {
                        'color': '#000',
                        'padding': [2, 0, 0, 0] # Đẩy chữ xuống dưới tick một chút
                    },
                    'tick': {
                        'width': 1, # Độ dày tick
                        'height': 5, # Độ dài tick
                        'backgroundColor': '#000',
                        'align': 'center'
                    }
                }
            }
        },
        'yAxis': {
            'type': 'value',
            'name': y_axis_unit,
            'nameLocation': 'end',
            'nameGap': 12,
            'nameTextStyle': {
                'fontSize': 13,
                'fontWeight': 'bold'
            },
            'min': axis_min,
            'max': axis_max_extended,  # Trục dài hơn để vẽ mũi tên
            'interval': interval,
            'axisLine': {
                'show': True,
                'symbol': ['none', 'arrow'], # Vẽ mũi tên chuẩn
                'symbolSize': [8, 12],
                'lineStyle': {
                    'color': '#000'
                }
            },
            'axisTick': {
                'show': False # Tắt tick mặc định
            },
            'axisLabel': {
                'color': '#000',
                'fontSize': 12,
                'formatter': 'FORMATTER_PLACEHOLDER', # Sẽ chèn hàm JS vào đây
                'margin': 0, # Kéo label sát vào trục để tick giả chạm trục
                'rich': {
                    'value': {
                        'color': '#000',
                        'padding': [0, 2, 0, 0] # Khoảng cách giữa số và tick giả
                    },
                    'tick': {
                        'width': 5, # Độ dài tick
                        'height': 1, # Độ dày tick
                        'backgroundColor': '#000', # Màu tick
                        'align': 'right'
                    }
                }
            },
            'splitLine': {
                'show': False,
                'lineStyle': {
                    'type': 'dashed',
                    'color': '#ddd'
                }
            }
        },
        'series': echarts_series
    }
    
    # Add source if provided
    if 'source' in user_options:
        option['graphic'] = [{
            'type': 'text',
            'left': 'center',
            'bottom': '2%', # Đặt Source thấp nhất
            'style': {
                'text': user_options['source'],
                'fontSize': 11,
                'fontStyle': 'italic'
            }
        }]
    
    return option
