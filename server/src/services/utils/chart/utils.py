"""
Utility functions for GenChart - ECharts Option Generator
Các hàm dùng chung cho tất cả các loại biểu đồ
"""


def find_min_max(data_list):
    """
    Tìm giá trị min và max từ danh sách dữ liệu
    
    Args:
        data_list: List các số hoặc list of lists
        
    Returns:
        tuple: (min_value, max_value)
    """
    flat_data = []
    
    if not data_list:
        return 0, 0
    
    # Flatten nested lists
    for item in data_list:
        if isinstance(item, (list, tuple)):
            flat_data.extend(item)
        else:
            flat_data.append(item)
    
    if not flat_data:
        return 0, 0
    
    return min(flat_data), max(flat_data)


def calculate_percentage(value, total):
    """
    Tính phần trăm
    
    Args:
        value: Giá trị cần tính %
        total: Tổng giá trị
        
    Returns:
        float: Phần trăm (0-100)
    """
    if total == 0:
        return 0
    return (value / total) * 100


def format_number(num, precision=2):
    """
    Format số theo định dạng Việt Nam
    
    Args:
        num: Số cần format
        precision: Số chữ số thập phân
        
    Returns:
        str: Số đã format
    """
    if num is None:
        return "0"
    
    if isinstance(num, float):
        if num == int(num):
            return str(int(num))
        return f"{num:.{precision}f}".rstrip('0').rstrip('.')
    
    return str(num)

def get_pattern_styles():
    """
    Trả về danh sách pattern styles để thay thế màu sắc
    Patterns: chấm bi, sọc chéo, zigzag, caro, kẻ ngang, kẻ dọc, etc.
    
    Returns:
        list: Danh sách dict chứa pattern config
    """
    return [
        {'type': 'dots', 'name': 'Chấm bi'},
        {'type': 'diagonal', 'name': 'Sọc chéo'},
        {'type': 'zigzag', 'name': 'Zigzag'},
        {'type': 'cross', 'name': 'Caro'},
        {'type': 'horizontal', 'name': 'Kẻ ngang'},
        {'type': 'vertical', 'name': 'Kẻ dọc'},
        {'type': 'grid', 'name': 'Lưới'},
        {'type': 'diagonal_reverse', 'name': 'Sọc chéo ngược'},
    ]


def create_pattern_js_function():
    """
    Trả về JavaScript function để tạo pattern
    Dùng cho HTML generation
    
    Returns:
        str: JavaScript code
    """
    return """
function createPattern(type) {
    let canvas = document.createElement("canvas");
    let ctx = canvas.getContext("2d");
    canvas.width = 16;
    canvas.height = 16;

    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, 16, 16);
    ctx.strokeStyle = "#000";
    ctx.fillStyle = "#000";
    ctx.lineWidth = 1;

    if (type === "dots") {
        // Chấm bi
        ctx.beginPath();
        ctx.arc(4, 4, 1.5, 0, Math.PI * 2);
        ctx.arc(12, 12, 1.5, 0, Math.PI * 2);
        ctx.fill();
    } else if (type === "diagonal") {
        // Sọc chéo
        ctx.beginPath();
        ctx.moveTo(0, 16);
        ctx.lineTo(16, 0);
        ctx.moveTo(-8, 8);
        ctx.lineTo(8, -8);
        ctx.moveTo(8, 24);
        ctx.lineTo(24, 8);
        ctx.stroke();
    } else if (type === "zigzag") {
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
    } else if (type === "cross") {
        // Caro
        ctx.fillStyle = "#ddd";
        ctx.fillRect(0, 0, 16, 16);
        ctx.strokeStyle = "#000";
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(16, 16);
        ctx.moveTo(16, 0);
        ctx.lineTo(0, 16);
        ctx.stroke();
    } else if (type === "horizontal") {
        // Kẻ ngang
        ctx.beginPath();
        ctx.moveTo(0, 4);
        ctx.lineTo(16, 4);
        ctx.moveTo(0, 12);
        ctx.lineTo(16, 12);
        ctx.stroke();
    } else if (type === "vertical") {
        // Kẻ dọc
        ctx.beginPath();
        ctx.moveTo(4, 0);
        ctx.lineTo(4, 16);
        ctx.moveTo(12, 0);
        ctx.lineTo(12, 16);
        ctx.stroke();
    } else if (type === "grid") {
        // Lưới
        ctx.beginPath();
        ctx.moveTo(0, 8);
        ctx.lineTo(16, 8);
        ctx.moveTo(8, 0);
        ctx.lineTo(8, 16);
        ctx.stroke();
    } else if (type === "diagonal_reverse") {
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
"""


def calculate_axis_interval(min_val, max_val, preferred_intervals=5, force_min_zero=True):
    """
    Tính khoảng cách đều nhau cho trục tung
    Đảm bảo các con số tròn, dễ đọc
    
    Args:
        min_val: Giá trị nhỏ nhất
        max_val: Giá trị lớn nhất
        preferred_intervals: Số khoảng chia mong muốn (Mặc định: 5 khoảng cho thoáng)
        force_min_zero: Có ép mốc min về 0 hay không nếu min > 0
        
    Returns:
        tuple: (min_axis, max_axis, interval)
    """
    if max_val == min_val:
        return 0, max_val * 1.2 if max_val > 0 else 100, 10
    
    # Tính range
    data_range = max_val - min_val
    if data_range == 0: # Tránh lỗi chia cho 0
        data_range = max_val if max_val > 0 else 10
        
    # Tính interval thô
    raw_interval = data_range / preferred_intervals
    
    # Làm tròn interval thành số đẹp
    magnitude = 10 ** len(str(int(raw_interval))) // 10 if raw_interval >= 1 else 1
    if magnitude == 0:
        magnitude = 1
    
    nice_intervals = [1, 2, 5, 10, 20, 25, 50, 100]
    interval = magnitude
    
    for nice in nice_intervals:
        test_interval = nice * magnitude
        if test_interval >= raw_interval:
            interval = test_interval
            break
    
    # Tính min và max của trục
    axis_min = (min_val // interval) * interval
    
    if force_min_zero:
        if axis_min > 0 and axis_min - interval >= 0:
            axis_min -= interval
        elif axis_min > 0:
            axis_min = 0
    else:
        # Hạ mốc min xuống 1 khoảng interval để biểu đồ cách đáy một đoạn đẹp
        if axis_min > 0 and axis_min - interval > 0:
            axis_min -= interval
    
    axis_max = ((max_val // interval) + 1) * interval
    if axis_max < max_val:
        axis_max += interval
    
    return axis_min, axis_max, interval


def validate_chart_data(data):
    """
    Validate dữ liệu đầu vào cho biểu đồ
    
    Args:
        data: Dict chứa dữ liệu biểu đồ
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data phải là dict"
    
    if 'data' not in data:
        return False, "Thiếu key 'data'"
    
    chart_data = data['data']
    
    if 'series' not in chart_data:
        return False, "Thiếu key 'series' trong data"
    
    if not isinstance(chart_data['series'], list):
        return False, "series phải là list"
    
    if len(chart_data['series']) == 0:
        return False, "series không được rỗng"
    
    # Validate từng series
    for i, series in enumerate(chart_data['series']):
        if not isinstance(series, dict):
            return False, f"series[{i}] phải là dict"
        
        if 'data' not in series:
            return False, f"series[{i}] thiếu key 'data'"
        
        if not isinstance(series['data'], list):
            return False, f"series[{i}].data phải là list"
    
    return True, ""


def merge_options(default_options, user_options):
    """
    Merge user options vào default options
    
    Args:
        default_options: Dict options mặc định
        user_options: Dict options từ người dùng (có thể None)
        
    Returns:
        dict: Options đã merge
    """
    if not user_options:
        return default_options
    
    result = default_options.copy()
    
    for key, value in user_options.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_options(result[key], value)
        else:
            result[key] = value
    
    return result
