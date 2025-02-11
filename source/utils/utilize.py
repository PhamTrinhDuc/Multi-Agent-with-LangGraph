import json
import os


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


def compute_args_hash():
    pass