import ast


def parse_string_to_dict(input_string: str) -> dict:
    """
        Nhận string từ function calling trả về, xử lí string và đưa về dạng dictionary chứa thông tin của các thông số kĩ thuật.
        Dictionary này sẽ là đầu vào cho cho các hàm search đóng vai trò như filter
        Args:
            - input_string: string trả về từ function calling
        Return:
            
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
        return f"Error: Invalid input string - {str(e)}"
    
def get_keywords():
    pass 

def parse_specification_range():
    pass 