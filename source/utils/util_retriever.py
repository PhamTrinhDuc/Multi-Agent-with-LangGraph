import ast
import re 
from typing import Dict, Any, Literal, Tuple 

def parse_string_to_dict(input_string: str) -> Dict[str, Any]:
    """
        Nhận string từ function calling trả về, xử lí string và đưa về dạng dictionary chứa thông tin của các thông số kĩ thuật.
        Dictionary này sẽ là đầu vào cho cho các hàm search đóng vai trò như filter
        Args:
            - input_string: string trả về từ function calling
        Return:
            - input ở dạng dictionary
    """
    try:
        # Thay thế các giá trị rỗng bằng None để ast có thể xử lý
        input_string = input_string.replace('""', 'None')
        data_dict = ast.literal_eval(input_string)
        
        # Chuyển lại None thành chuỗi rỗng nếu cần
        for key, value in data_dict.items():
            if value is None:
                data_dict[key] = ""
        return data_dict
    except (SyntaxError, ValueError) as e:
        raise ValueError(f"Error: Invalid input string - {str(e)}")
    
def parse_specification_range(specification: str):
    """
    Phân tích chuỗi thông số kỹ thuật và trả về khoảng giá trị min_value, max_value.
    Args:
        - specification: Chuỗi thông số kỹ thuật cần xử lý.
    Returns:
        - Tuple (min_value, max_value): Khoảng giá trị tìm kiếm.
    """

    # Step 1: Trích xuất số và đơn vị
    number_pattern = r"(?P<number>\d+(?:,\d+)*)"  # Pattern để trích xuất số
    unit_pattern = r"(?P<unit>triệu|nghìn|tr|k|kg|l|lít|kw|w|t|btu)\b"  # Pattern để trích xuất đơn vị

    numbers = [float(num.replace(',', '')) for num in re.findall(number_pattern, specification)]
    units = re.findall(unit_pattern, specification, re.IGNORECASE)
    unit = units[-1].lower() if units else None  # Lấy đơn vị cuối cùng làm đơn vị chung

    # Step 2: Chuyển đổi số dựa trên đơn vị
    def convert_number_with_unit(number, unit) -> float:
        """Chuyển đổi một số dựa trên đơn vị."""
        if unit in ['triệu', 'tr', 't']:
            return number * 1000000
        elif unit in ['nghìn', 'k']:
            return number * 1000
        elif unit in ['kw']:
            return number * 1000
        return number  # Không có đơn vị, giữ nguyên giá trị

    converted_numbers = [convert_number_with_unit(num, unit) for num in numbers]

    # Step 3: Xây dựng khoảng giá trị
    if not converted_numbers:
        return 0, 999999999  # Giá trị mặc định nếu không có số nào

    if len(converted_numbers) == 1:
        # Nếu chỉ có một số, tạo khoảng ±20%
        value = converted_numbers[0]
        return value * 0.8, value * 1.2
    else:
        # Nếu có nhiều số, lấy khoảng giữa số nhỏ nhất và lớn nhất
        return min(converted_numbers), max(converted_numbers)