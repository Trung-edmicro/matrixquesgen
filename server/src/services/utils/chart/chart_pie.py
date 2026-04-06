"""
Pie Chart Generator for GenChart
Tạo biểu đồ tròn (Pie Chart) theo quy tắc lý thuyết vẽ biểu đồ
"""

from services.utils.chart.utils import (
    calculate_percentage,
    get_pattern_styles,
    validate_chart_data,
    create_pattern_js_function
)


def generate_pie_chart(data):
    """
    Tạo ECharts option cho biểu đồ tròn
    
    Quy tắc theo lý thuyết:
    - Bắt đầu từ 12 giờ (startAngle = 90)
    - Vẽ theo chiều kim đồng hồ (clockwise = true)
    - 360° = 100%, mỗi 1% = 3.6°
    - Hiển thị % cho mỗi phần
    - Nếu % quá nhỏ, ghi chú ở ngoài (labelLine)
    - Có thể vẽ nhiều biểu đồ tròn cùng lúc (so sánh quy mô)
    
    Args:
        data: Dict với format:
        {
            "chart_type": "pie",
            "data": {
                "series": [
                    {
                        "name": "Cơ cấu GDP 2023",
                        "data": [
                            {"name": "Nông nghiệp", "value": 12.5},
                            {"name": "Công nghiệp", "value": 37.6},
                            {"name": "Dịch vụ", "value": 42.4},
                            {"name": "Thuế", "value": 7.5}
                        ]
                    }
                ]
            },
            "options": {  # Optional
                "title": "CƠ CẤU GDP",
                "subtitle": "Năm 2023",
                "show_legend": True,
                "show_percentage": True,
                "radius": "60%",  # Hoặc ["40%", "70%"] cho donut
                "center": ["50%", "50%"]  # Vị trí tâm
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
    
    # Extract series
    series_list = chart_data['series']
    
    # Get pattern styles
    pattern_styles = get_pattern_styles()
    
    # Build series
    echarts_series = []
    
    for idx, series in enumerate(series_list):
        series_name = series.get('name', f'Series {idx + 1}')
        series_data = series.get('data', [])
        
        # Calculate total for percentage
        total = sum(item['value'] for item in series_data if isinstance(item, dict))
        
        # Format data with percentage and pattern
        formatted_data = []
        for i, item in enumerate(series_data):
            if isinstance(item, dict):
                value = item['value']
                percentage = calculate_percentage(value, total)
                pattern_type = pattern_styles[i % len(pattern_styles)]['type']
                formatted_data.append({
                    'name': item['name'],
                    'value': value,
                    'percentage': percentage,
                    '_patternType': pattern_type
                })
        
        # Determine radius and center for multiple pies
        if len(series_list) == 1:
            radius = user_options.get('radius', '60%')
            # Đẩy pie lên trên để cân bằng với title/legend ở dưới
            center = user_options.get('center', ['50%', '40%'])  # Từ 50% xuống 40%
        else:
            # Multiple pies - arrange horizontally with proper spacing
            # Với 2 pies, để legend ở right 3%, pie không được vượt quá 92%
            # Formula: center + radius <= 92%
            # Nếu radius 35%, center tối đa = 57%
            # Spacing: [28%, 56%] cho 2 pies
            if len(series_list) == 2:
                # Tối ưu cho 2 pies - giảm size và tăng khoảng cách
                # Pie 1: 26% ± 36% = [-10%, 62%], Pie 2: 64% ± 36% = [28%, 100%]
                # Legend at 97%, so Pie 2 right edge at 100% is tight but OK
                centers = [['26%', '40%'], ['64%', '40%']]
                center = centers[idx]
                radius = user_options.get('radius', '38%')  # Giảm từ 40% xuống 36%
            else:
                # General case cho 3+ pies
                spacing = 100 / (len(series_list) + 1)
                center = [f'{spacing * (idx + 1)}%', '40%']
                radius = user_options.get('radius', '30%')
        
        show_percentage = user_options.get('show_percentage', True)
        
        series_config = {
            'name': series_name,
            'type': 'pie',
            'radius': radius,
            'center': center,
            'startAngle': 90,  # Bắt đầu từ 12 giờ
            'clockwise': True,  # Theo chiều kim đồng hồ
            'data': formatted_data,
            'label': {
                'show': True,
                'position': 'inside',
                'formatter': '{d}%',
                'fontSize': 15,
                'fontWeight': 'bold',
                'color': '#000',
                'backgroundColor': '#fff'
            },
            'labelLine': {
                'show': False,
                'length': 15,
                'length2': 10,
                'lineStyle': {
                    'color': '#000',
                    'width': 1
                }
            },
            'itemStyle': {
                'borderColor': '#000',
                'borderWidth': 1
            },
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 10,
                    'shadowOffsetX': 0,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)'
                }
            }
        }
        
        echarts_series.append(series_config)
    
    # Build legend data from first series
    legend_data = [item['name'] for item in series_list[0].get('data', [])]
    
    # Configure titles
    titles = []
    
    # Main title - nâng cao lên dưới pie
    titles.append({
        'text': user_options.get('title', ''),
        'subtext': user_options.get('subtitle', ''),
        'left': 'center',
        'bottom': '18%',  # Đặt phía dưới pie
        'textStyle': {
            'fontSize': 16,
            'fontWeight': 'bold'
        },
        'subtextStyle': {
            'fontSize': 14,
            'fontStyle': 'italic'
        }
    })
    
    # Sub titles for each pie if multiple - đặt dưới pie, căn giữa theo center của pie
    if len(series_list) > 1:
        for idx, series in enumerate(series_list):
            if len(series_list) == 2:
                # Với 2 pies, sử dụng centers cố định khớp với pie centers
                title_centers = ['26%', '64%']
                title_left = title_centers[idx]
            else:
                # General case cho 3+ pies
                spacing = 100 / (len(series_list) + 1)
                title_left = f'{spacing * (idx + 1)}%'
            
            titles.append({
                'text': series.get('name', ''),
                'left': title_left,
                'bottom': '28%',  # Dưới pie
                'textAlign': 'center',
                'textStyle': {
                    'fontSize': 14,
                    'fontWeight': 'bold',
                }
            })
    
    # Build chart option
    option = {
        'textStyle': {
            'fontFamily': 'Roboto, sans-serif'
        },
        'title': titles,
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: {c} ({d}%)'
        },
        'legend': {
            'data': legend_data,
            'show': user_options.get('show_legend', True),
            'top': 'center', # Hiển thị ở giữa theo chiều dọc
            'right': '3%' if len(series_list) > 1 else '5%', # Tăng margin để tránh đè pie
            'orient': 'vertical' # Xếp dọc
        },
        'series': echarts_series
    }
    
    # Graphics for unit and source
    graphics = []
    
    # Determine unit - LUÔN hiển thị unit cho pie chart (mặc định là %)
    unit = user_options.get('unit')
    if not unit and series_list:
        # Kiểm tra series có unit không, nếu không thì default '%'
        unit = series_list[0].get('unit')
    if not unit:
        unit = '%'  # Default unit cho pie chart
        
    # LUÔN hiển thị unit cho pie chart
    if True:  # Always show unit for pie charts
        unit_graphic = {
            'type': 'text',
            'style': {
                'text': f'({unit})', # Thêm ngoặc đơn bao quanh đơn vị
                'fontSize': 20,
                'fontStyle': 'italic',
                'fontWeight': 'bold'
            }
        }
        if len(series_list) == 1:
            # Single pie: top right (kéo sang trái một chút để tránh đè legend nếu có)
            unit_graphic['right'] = '30%'
            unit_graphic['top'] = '20%'
        else:
            # Multiple pies: ở giữa canvas theo cả 2 chiều (giữa 2 pies)
            unit_graphic['left'] = 'center'
            unit_graphic['top'] = '15%'
            
        graphics.append(unit_graphic)

    # Add source if provided - dưới main title
    if 'source' in user_options:
        graphics.append({
            'type': 'text',
            'left': 'center',
            'bottom': '10%',
            'style': {
                'text': user_options['source'],
                'fontSize': 13,
                'fontStyle': 'italic',
            }
        })
        
    if graphics:
        option['graphic'] = graphics
    
    return option
