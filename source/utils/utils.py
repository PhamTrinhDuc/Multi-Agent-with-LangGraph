import json
import os
import ast
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any, Literal

def format_message(role: Literal['system', 'user'], 
                   content: str): 
    if role == 'system': 
        return {"role": role, 'content': SystemMessage(content=content)}
    elif role == 'user': 
        return {'role': role, 'content': HumanMessage(content=content)}
    elif role == 'ai': 
        return {'role': role, 'content': AIMessage(content=content)}
    else:
        raise ValueError(f"Không support role: {role}.")

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

def save_conversation(self, 
                      phone_number: str, 
                      id_request: str,
                      query: str, response: str) -> None:
    conversation_key = f"{id_request}.json"
    os.makedirs(os.path.join(self.CONVERSATION_PATH, phone_number), exist_ok=True)
    user_specific_conversation = os.path.join(self.CONVERSATION_PATH, phone_number, conversation_key)
    
    # mở file đã lưu lịch sử trò chuyện
    if os.path.exists(user_specific_conversation) and os.path.getsize(user_specific_conversation) > 0:
        with open(user_specific_conversation, mode='r', encoding='utf-8') as f:
            conversation = json.load(f)
    else:
        conversation = {}

    # lưu lại cuộc trò chuyện mới vào file json
    if not id_request in conversation:
        conversation[id_request] = []
    conversation[id_request].append({"human": query, "ai": response})

    with open(user_specific_conversation, mode='w', encoding='utf-8') as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)

def load_conversation(self, conv_user: str, id_request: str) -> str:
    """
    Lấy lịch sử cuộc hội thoại được lưu trữ trong file json. Lấy ra 3 cuộc hội thoại gần nhất.
    Args:
        user_name: str: tên người dùng
        seasion_id: str: id của phiên hội thoại
    Returns:
        history: List[Dict]: lịch sử cuộc hội thoại
    """
    if not conv_user or not id_request:
        return []
    else:
        history = []
        conversation_key = f"{id_request}.json"
        os.makedirs(os.path.join(self.CONVERSATION_PATH, conv_user), exist_ok=True)
        user_specific_conversation = os.path.join(self.CONVERSATION_PATH, conv_user, conversation_key)
        if os.path.exists(user_specific_conversation) and os.path.getsize(user_specific_conversation) > 0:
            try:
                with open(user_specific_conversation, 'r') as f:
                    conversation = json.load(f)
                    if id_request in conversation:
                        conversation =  conversation[id_request][-5:]
                        for conv in conversation:
                            conv['human'] = self._clean_html(conv['human'])
                            conv['ai'] = self._clean_html(conv['ai'])
                        return conversation
                    else:
                        return []
            except json.JSONDecodeError as e :
                print("LOAD CONVERSATION ERROR: ", e)
                return []
        else: 
            return []