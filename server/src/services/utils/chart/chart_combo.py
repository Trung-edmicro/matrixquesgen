"""
Combo Chart Generator for GenChart
Tạo biểu đồ kết hợp (Cột và Đường) theo quy tắc lý thuyết vẽ biểu đồ
"""

import json
from services.utils.chart.utils import (
    find_min_max,
    calculate_axis_interval,
    validate_chart_data,
    get_pattern_styles,
    create_pattern_js_function
)

def generate_combo_chart(data):
    """
    Tạo ECharts option cho biểu đồ kết hợp (Combo Chart)
    
    Quy tắc:
    - 2 trục tung: Trái cho Cột, Phải cho Đường.
    - Đánh số chuẩn trên 2 trục tung cách đều nhau (2 trục độc lập).
    - Cột đầu tiên cách trục tung 0.5 - 1.0 cm.
    - Điểm của Đường nằm chính giữa cột.
    
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
    
    # Phân loại series thành cột (bar) và đường (line)
    bar_series = []
    line_series = []
    
    bar_unit = ""
    line_unit = ""
    
    for s in series_list:
        if s.get('type', 'bar') == 'bar':
            bar_series.append(s)
            if not bar_unit and 'unit' in s:
                bar_unit = s['unit']
        else:
            line_series.append(s)
            if not line_unit and 'unit' in s:
                line_unit = s['unit']
                
    # fallback unit nếu không có
    if not bar_unit: bar_unit = user_options.get('y_axis_left_unit', '')
    if not line_unit: line_unit = user_options.get('y_axis_right_unit', '')

    # Tính toán trục Y trái (Bar)
    bar_values = [s['data'] for s in bar_series]
    bar_style = user_options.get('bar_style', 'stacked')
    
    if bar_values:
        if bar_style == 'stacked' and len(bar_values) > 1:
            # Tính tổng theo từng cột để tìm max khi xếp chồng
            stacked_sums = []
            for i in range(len(bar_values[0])):
                # Xử lý an toàn nếu dữ liệu không đều hoặc có '-' (nội suy)
                col_sum = 0
                for series_data in bar_values:
                    if i < len(series_data):
                        val = series_data[i]
                        if isinstance(val, (int, float)):
                            col_sum += val
                stacked_sums.append(col_sum)
            bar_min = 0 # Cột chồng thường bắt đầu từ 0
            bar_max = max(stacked_sums) if stacked_sums else 100
        else:
            bar_min, bar_max = find_min_max(bar_values)
    else:
        bar_min, bar_max = 0, 100
        
    axis_min_l, axis_max_l, interval_l = calculate_axis_interval(bar_min, bar_max)
    axis_max_extended_l = axis_max_l + interval_l * 0.5
    axis_max_display_l = axis_max_l
    
    # Tính toán trục Y phải (Line)
    line_values = [s['data'] for s in line_series]
    line_min, line_max = find_min_max(line_values) if line_values else (0, 100)
    # Bắt đầu từ 0 giống trục trái để tương thích với quy tắc vẽ biểu đồ
    axis_min_r, axis_max_r, interval_r = calculate_axis_interval(line_min, line_max, force_min_zero=True)
    axis_max_extended_r = axis_max_r + interval_r * 0.5
    axis_max_display_r = axis_max_r

    # Styles
    pattern_styles = get_pattern_styles()
    symbols = ['circle', 'rect', 'triangle', 'diamond', 'pin']
    
    echarts_series = []
    legend_data = []
    
    bar_style = user_options.get('bar_style', 'stacked')
    show_labels = user_options.get('show_data_labels', True)
    
    # Render Bar series
    for idx, s in enumerate(bar_series):
        pattern_type = pattern_styles[idx % len(pattern_styles)]['type']
        s_name = s.get('name', f'Bar {idx + 1}')
        legend_data.append(s_name)
        
        s_config = {
            'name': s_name,
            'type': 'bar',
            'yAxisIndex': 0,
            'data': s['data'],
            'barWidth': '20%',  # Combo chart: cột hẹp (20% = 1/2 width so với bar chart 40%)
            'barGap': '0%' if bar_style == 'grouped' and len(bar_series) > 1 else '30%',
            'label': {
                'show': show_labels,
                'position': 'top' if bar_style != 'stacked' else 'inside',
                'formatter': 'FORMATTER_LABEL_PLACEHOLDER_COMBO',
                'fontSize': 12,
                'color': '#000',
                'fontWeight': 'bold',
                'backgroundColor': '#fff',
                'padding': 0,
                'borderRadius': 2
            },
            'itemStyle': {
                'color': f'PATTERN_PLACEHOLDER_{pattern_type}',
                'borderColor': '#000',
                'borderWidth': 1
            },
            '_patternType': pattern_type
        }
        if bar_style == 'stacked':
            s_config['stack'] = 'total'
            
        echarts_series.append(s_config)
        
    # Render Line series
    for idx, s in enumerate(line_series):
        s_name = s.get('name', f'Line {idx + 1}')
        legend_data.append(s_name)
        
        s_config = {
            'name': s_name,
            'type': 'line',
            'yAxisIndex': 1,
            'data': s['data'],
            'connectNulls': True, # Nối liền các điểm qua các đoạn dữ liệu rỗng
            'symbol': symbols[idx % len(symbols)],
            'symbolSize': 8,
            'label': {
                'show': show_labels,
                'position': 'top',
                'formatter': 'FORMATTER_LABEL_PLACEHOLDER_COMBO',
                'fontSize': 12,
                'color': '#000',
                'fontWeight': 'bold',
                'backgroundColor': '#fff',
                'padding': 0,
                'borderRadius': 2
            },
            'lineStyle': {
                'width': 2.5,
                'color': '#000'
            },
            'itemStyle': {
                'color': '#fff',
                'borderColor': '#000',
                'borderWidth': 2
            }
        }
        echarts_series.append(s_config)

    # Tính toán khoảng cách (gap) giữa các năm nếu người dùng nhập số
    try:
        num_categories = [int(cat) for cat in categories]
        # Kiểm tra xem danh sách đã được sắp xếp chưa, nếu đúng thì là các mốc năm
        if sorted(num_categories) == num_categories and len(num_categories) > 1:
            # Tìm khoảng cách nhỏ nhất giữa 2 năm liên tiếp
            diffs = [num_categories[i+1] - num_categories[i] for i in range(len(num_categories)-1)]
            min_diff = min(diffs)
            
            # Cấu hình "bước nhảy mốc". Để tránh tạo quá nhiều cột rỗng
            # Ta quy ước min_diff tương đương 1 "khoảng" rỗng nhỏ nhất.
            # Với khoảng cách lớn hơn, số lượng cột rỗng = (diff / min_diff) - 1
            
            full_categories = []
            full_data_matrix = {i: [] for i in range(len(echarts_series))}
            
            for i in range(len(categories)):
                current_year = categories[i]
                full_categories.append(current_year)
                
                # Copy dữ liệu thật
                for s_idx, series in enumerate(echarts_series):
                    full_data_matrix[s_idx].append(series['data'][i])
                
                # Nếu chưa phải năm cuối, nội suy khoảng rỗng tới năm tiếp theo
                if i < len(categories) - 1:
                    gap = diffs[i]
                    # Số lượng slot rỗng cần chèn (scale theo min_diff, làm tròn số)
                    # Dùng max(0) để nếu gap bằng min_diff thì không chèn thêm (giữ 1 khoảng chuẩn)
                    # Nếu gap lớn hơn (vd 5 so với 2), (5/2)-1 = 1.5 -> chèn 1 slot rỗng
                    empty_slots = max(0, int(round((gap / min_diff) - 1)))
                    
                    for _ in range(empty_slots):
                        full_categories.append(f"_{current_year}_{_}") # Tên giả để không trùng
                        for s_idx in range(len(echarts_series)):
                            full_data_matrix[s_idx].append(None)
            
            # Cập nhật lại series
            for s_idx, series in enumerate(echarts_series):
                series['data'] = full_data_matrix[s_idx]
                
            categories = full_categories
    except ValueError:
        pass # Không phải số thì giữ nguyên
        
    x_axis_unit = user_options.get('x_axis_unit', 'năm')

    option = {
        'textStyle': {
            'fontFamily': 'Roboto, sans-serif'
        },
        'title': {
            'text': user_options.get('title', ''),
            'subtext': user_options.get('subtitle', ''),
            'left': 'center',
            'bottom': '12%',
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
            'show': user_options.get('show_legend', True),
            'bottom': '20%',
            'left': 'center',
            'icon': "rect",
            'itemWidth': 28,
            'itemHeight': 14,
            'itemGap': 20,
            'textStyle': {
                'fontSize': 14,
                'fontWeight': 'bold'
            }
        },
        'grid': {
            'left': 80,
            'right': 220,  # Tăng từ 120 lên 220 để chứa mốc trục tung phải và mũi tên trục hoành kéo dài
            'top': 40,
            'bottom': 180,  # Tăng từ 160 lên 180 để tạo khoảng trống cho đơn vị trục hoành
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': categories,
            'name': x_axis_unit,
            'nameLocation': 'end',
            'nameGap': 50,
            'nameTextStyle': {
                'fontSize': 13
            },
            'axisLine': {
                'show': True,
                'symbol': ['none', 'arrow'],
                'symbolSize': [8, 12],
                'symbolOffset': [0, 40],
                'lineStyle': {
                    'color': '#000'
                }
            },
            'axisTick': {
                'show': False
            },
            'axisLabel': {
                'color': '#000',
                'fontSize': 12,
                'margin': 12,
                'interval': 'FORMATTER_X_INTERVAL_PLACEHOLDER' # Sẽ xử lý JS để ẩn các nhãn năm trống
            }
        },
        'yAxis': [
            {
                # Left Y-Axis for Bar
                'type': 'value',
                'name': bar_unit,
                'nameLocation': 'end',
                'nameGap': 12,
                'nameTextStyle': {
                    'fontSize': 13,
                    'fontWeight': 'bold'
                },
                'min': axis_min_l,
                'max': axis_max_extended_l,
                'interval': interval_l,
                'axisLine': {
                    'show': True,
                    'symbol': ['none', 'arrow'],
                    'symbolSize': [8, 12],
                    'lineStyle': {
                        'color': '#000',
                        'width': 1.5
                    }
                },
                'axisTick': {
                    'show': False
                },
                'axisLabel': {
                    'color': '#000',
                    'fontSize': 12,
                    'formatter': 'FORMATTER_Y_LEFT_PLACEHOLDER',
                    'margin': 0,
                    'rich': {
                        'value': {
                            'color': '#000',
                            'padding': [0, 2, 0, 0]
                        },
                        'tick': {
                            'width': 5,
                            'height': 1,
                            'backgroundColor': '#000',
                            'align': 'right'
                        }
                    }
                },
                'splitLine': {
                    'show': False
                }
            },
            {
                # Right Y-Axis for Line
                'type': 'value',
                'name': line_unit,
                'nameLocation': 'end',
                'nameGap': 12,
                'nameTextStyle': {
                    'fontSize': 13,
                    'fontWeight': 'bold'
                },
                'min': axis_min_r,
                'max': axis_max_extended_r,
                'interval': interval_r,
                'axisLine': {
                    'show': True,
                    'symbol': ['none', 'arrow'],
                    'symbolSize': [8, 12],
                    'lineStyle': {
                        'color': '#000'
                    }
                },
                'axisTick': {
                    'show': False
                },
                'axisLabel': {
                    'color': '#000',
                    'fontSize': 12,
                    'formatter': 'FORMATTER_Y_RIGHT_PLACEHOLDER',
                    'margin': 0,
                    'rich': {
                        'value': {
                            'color': '#000',
                            'padding': [0, 0, 0, 2]
                        },
                        'tick': {
                            'width': 5,
                            'height': 1,
                            'backgroundColor': '#000',
                            'align': 'left'
                        }
                    }
                },
                'splitLine': {
                    'show': False
                }
            }
        ],
        'series': echarts_series
    }
    
    # Add source if provided
    if 'source' in user_options:
        option['graphic'] = [{
            'type': 'text',
            'left': 'center',
            'bottom': '7%',
            'style': {
                'text': user_options['source'],
                'fontSize': 11,
                'fontStyle': 'italic'
            }
        }]
    else:
        option['graphic'] = []
    
    # Thêm vị trí chính xác của axisLine và thông tin vẽ tick mark
    # Backend tính toán sẵn để React không phải scan canvas
    canvas_height = user_options.get('canvas_height', 550)  # Default chart height
    grid_bottom = option['grid']['bottom']
    axis_line_y_pos = canvas_height - grid_bottom  # Vị trí y của axisLine
    
    # Lưu vị trí để React sử dụng trực tiếp
    option['_draw_connector_line'] = {
        'enabled': True,
        'axis_line_y': axis_line_y_pos,  # Vị trí chính xác của axisLine trong canvas
        'symbol_offset_y': option['xAxis']['axisLine']['symbolOffset'][1],  # y-offset của mũi tên
        'tick_length': 5  # Độ dài tick mark
    }
    
    # Store display max for HTML generation
    option['_axis_max_display_l'] = axis_max_display_l
    option['_axis_max_display_r'] = axis_max_display_r
    
    # Flag để React vẽ đường nối từ trục hoành đến mũi tên
    option['_draw_axis_connector'] = True
    
    return option
