"""
Bar Chart Generator for GenChart
Tạo biểu đồ cột (Bar Chart) theo quy tắc lý thuyết vẽ biểu đồ
"""

from services.utils.chart.utils import (
    find_min_max,
    get_pattern_styles,
    calculate_axis_interval,
    validate_chart_data,
    merge_options,
    create_pattern_js_function
)


def generate_bar_chart(data):
    """
    Tạo ECharts option cho biểu đồ cột
    
    Quy tắc theo lý thuyết:
    - Tỉ lệ: chiều cao trục tung = 2/3 chiều dài trục hoành
    - Cột đầu tiên cách trục tung 0.5-1.0 cm
    - Độ rộng các cột phải đều nhau
    - Đánh số chuẩn trên trục tung cách đều
    - Hiển thị số liệu trên đỉnh cột
    - Đơn vị rõ ràng cho cả 2 trục
    
    Args:
        data: Dict với format:
        {
            "chart_type": "bar",
            "data": {
                "categories": ["2020", "2021", "2022"],  # Trục X
                "series": [
                    {
                        "name": "Dân số",
                        "data": [100, 120, 150],
                        "unit": "triệu người"
                    }
                ]
            },
            "options": {  # Optional
                "title": "Biểu đồ dân số",
                "subtitle": "Giai đoạn 2020-2022",
                "show_legend": True,
                "show_data_labels": True,
                "bar_style": "grouped"  # "grouped" hoặc "stacked"
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
    
    # Find min/max for scaling
    all_values = [s['data'] for s in series_list]
    min_val, max_val = find_min_max(all_values)
    
    # Calculate axis
    axis_min, axis_max, interval = calculate_axis_interval(min_val, max_val)
    
    # Extend max for arrow
    axis_max_extended = axis_max + interval * 0.5
    axis_max_display = axis_max
    
    # Get pattern styles
    pattern_styles = get_pattern_styles()
    
    # Build series
    echarts_series = []
    bar_style = user_options.get('bar_style', 'grouped')
    show_labels = user_options.get('show_data_labels', True)
    
    for idx, series in enumerate(series_list):
        pattern_type = pattern_styles[idx % len(pattern_styles)]['type']
        
        series_config = {
            'name': series.get('name', f'Series {idx + 1}'),
            'type': 'bar',
            'data': series['data'],
            'barWidth': '50%' if len(series_list) == 1 else None,
            'barGap': '0%' if bar_style == 'grouped' and len(series_list) > 1 else '30%',  # Cột sát nhau
            'label': {
                'show': show_labels,
                'position': 'top' if bar_style != 'stacked' else 'inside',
                'formatter': 'FORMATTER_LABEL_PLACEHOLDER_BAR',
                'fontSize': 12,
                'color': '#000'
            },
            'itemStyle': {
                'borderColor': '#000',
                'borderWidth': 1
            },
            '_patternType': pattern_type  # Store for HTML generation
        }
        
        # Nếu stacked, thêm stack config
        if bar_style == 'stacked':
            series_config['stack'] = 'total'
        
        echarts_series.append(series_config)
    
    # Build legend
    legend_data = [s.get('name', f'Series {i+1}') for i, s in enumerate(series_list)]
    
    # Get unit from first series (or user can specify)
    y_axis_unit = series_list[0].get('unit', '') if series_list else ''
    x_axis_unit = user_options.get('x_axis_unit')
    
    # Build chart option
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
                'type': 'shadow'
            }
        },
        'legend': {
            'data': legend_data,
            'show': user_options.get('show_legend', True) and len(series_list) > 1,
            'bottom': '18%',
            'left': 'center',
            'textStyle': {
                'fontSize': 14,
                'fontWeight': 'bold'
            }
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
            'data': categories,
            'name': x_axis_unit,
            'nameLocation': 'end',
            'nameGap': 12,
            'nameTextStyle': {
                'fontSize': 13
            },
            'axisLine': {
                'show': True,
                'symbol': ['none', 'arrow'],  # Mũi tên ở cuối trục
                'symbolSize': [8, 12],
                'lineStyle': {
                    'color': '#000'
                }
            },
            'axisTick': {
                'show': False  # Không hiển thị mốc trên trục hoành
            },
            'axisLabel': {
                'color': '#000',
                'fontSize': 12,
                'interval': 'FORMATTER_X_INTERVAL_PLACEHOLDER', # Sẽ chèn hàm ẩn nhãn fake bằng JS
                'rotate': user_options.get('x_label_rotate', 0)
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
            'bottom': '2%',
            'style': {
                'text': user_options['source'],
                'fontSize': 12,
                'fontStyle': 'italic'
            }
        }]
    
    return option