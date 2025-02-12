import json
import os
from hashlib import md5  


def load_json(file_name: str) -> dict:
    """Read json file from path provided"""
    if not os.path.exists(file_name):
        return {}
    with open(file=file_name, encoding="utf-8", mode='r') as f:
        return json.load(f)


def write_json(json_obj: dict, file_name: str):
    """Write json object to path provided"""
    with open(file=file_name, encoding="utf-8", mode='w') as f:
        json.dump(json_obj, f, ensure_ascii=False, indent=4)

def set_environment():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "chatbot"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = "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"  # Update to your API key


def compute_args_hash(*args):
    """
    Chuyển các đối sô thành 1 chuỗi. Mã hóa chuỗi thành dạng byte sử dụng encode() với mã hóa utf-8..
    Tính toán hash MD5  của chuỗi byte đã mã hóa sử dụng hàm md5() từ thư viện hashlib.
    Args:
        *args: Các đối số đầu vào cần tính toán giá trị băm.
    Returns:
        str: Giá trị băm MD5 của các đối số đầu vào dưới dạng chuỗi hexdigest.
    """
    '''
    hash1 = compute_args_hash(1, 2, "hello") -> "(1, 2, 'hello')"
    print(hash1)  # Output: '5d41402abc4b2a76b9719d911017c592'
    '''
    return md5(str(args).encode()).hexdigest()


def compute_mdhash_id(content: str, prefix: str = ""):
    """
    Tính toán mã băm MD5 cho nội dung và thêm tiền tố (nếu có).
    Args:
        content (str): Nội dung cần tính toán mã băm.
        prefix (str, optional): Tiền tố thêm vào trước mã băm. Mặc định là chuỗi rỗng.
    Returns:
        str: Chuỗi mã băm MD5 của nội dung, kèm theo tiền tố (nếu có).
    """
    return prefix + md5(content.encode()).hexdigest()