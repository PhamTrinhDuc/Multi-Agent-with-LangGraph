import os
import dotenv
import pandas as pd 
from openai import OpenAI
from utils import parse_string_to_dict
from prompt import PROMPT_SYSTEM, FUNC_CALL_TOOLS

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def extract_info(client, 
                 model: str, 
                 query_user: str, 
                 tools_calling: list[dict],
                 prompt_sys: str=""):

    messages = [
        {'role': 'system', 'content': prompt_sys},
        {"role": "user", "content": query_user}]

    openai_response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools_calling,
            tool_choice="auto",  # auto is default, but we'll be explicit
        )
    arguments = openai_response.choices[0].message.tool_calls[0].function.arguments
    
    specifications = parse_string_to_dict(arguments)
    return specifications


def main():
    arguments = extract_info("Tôi muốn mua điều hòa từ 10 đến 12 triệu")
    print(arguments)
    for key, value in arguments.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()