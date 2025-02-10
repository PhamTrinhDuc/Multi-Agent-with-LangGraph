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
    
def get_keywords():
    pass 


def parse_specification_range(specification: str): 
    # 1: Trích xuất số và đơn vị

    # Pattern để trích xuất số
    number_pattern = r"(?P<number>\d+(?:,\d+)*)"

    # Pattern để trích xuất đơn vị
    unit_pattern = r"(?P<unit>triệu|nghìn|tr|k|kg|l|lít|kw|w|t|btu)\b"

    numbers = [float(num.replace(',', '')) for num in re.findall(number_pattern, specification)]

    # Trích xuất tất cả các đơn vị và chọn đơn vị cuối cùng làm đơn vị chung
    units = re.findall(unit_pattern, specification, re.IGNORECASE)
    unit = units[-1].lower() if units else None  # Lấy đơn vị cuối cùng

    # 2: Chuyển đổi số dựa trên đơn vị
    converted_numbers = []
    for number in numbers:
        if unit in ['triệu', 'tr', 't']:
            converted_numbers.append(number * 1000000)
        elif unit in ['nghìn', 'k']:
            converted_numbers.append(number * 1000)
        elif unit in ['kw']:
            converted_numbers.append(number * 1000)
        else:
            converted_numbers.append(number)  # Không có đơn vị, giữ nguyên giá trị
    
    # 3: Xây dựng khoảng giá trị
    if not converted_numbers:
        return 0, 1000000  # Giá trị mặc định nếu không có số nào

    if len(numbers) == 1:
        # Nếu chỉ có một số, tạo khoảng ±20%
        value = numbers[0]
        min_value = value * 0.8
        max_value = value * 1.2
    else:
        # Nếu có nhiều số, lấy khoảng giữa số nhỏ nhất và lớn nhất
        min_value = min(numbers)
        max_value = max(numbers)

    return min_value, max_value