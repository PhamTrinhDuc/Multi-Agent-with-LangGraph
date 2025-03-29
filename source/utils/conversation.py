import json
import os
import logging
from typing import Dict, List



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
                logging.ERROR("LOAD CONVERSATION ERROR: ", e)
                return []
        else: 
            return []