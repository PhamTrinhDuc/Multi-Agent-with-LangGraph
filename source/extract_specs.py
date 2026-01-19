import os
import dotenv
import re
import json
from loguru import logger
from openai import OpenAI
from groq import Groq
from typing import Literal
from source.utils.utils import parse_string_to_dict
from source.utils.config import Config
from source.prompt import PROMPT_SYSTEM, FUNC_CALL_TOOLS

def get_client(type_client: Literal["groq", 'openai']="groq"):
    if type_client == 'groq':
        client = Groq()
    elif type_client == 'openai':
        client = OpenAI()
    else: 
        raise ValueError(f"No support model: {type_client}")
    return client

def parse_groq_function_call(content: str):
    """Parse Groq's function call format: <function(func_name){json_args}</function>"""
    pattern = r'<function\((\w+)\)({.*?})</function>'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        func_name = match.group(1)
        args_str = match.group(2)
        return func_name, args_str
    return None, None

def extract_info(query_user: str,
                 tool_call: str,
                 prompt_sys: str=PROMPT_SYSTEM['prompt_extract_spec'],
                 type_client: Literal["groq", 'openai']="groq"):
    
    messages = [
        {'role': 'system', 'content': prompt_sys},
        {"role": "user", "content": query_user}
    ]

    response = None
    try:
        client = get_client(type_client=type_client)
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL if type_client=='groq' else Config.OPENAI_MODEL,
            messages=messages,
            tools=FUNC_CALL_TOOLS[tool_call],
            tool_choice="auto"
        )

    except Exception as e:
        logger.error(f"An error occurred while create client: [{type_client}]. Error: {str(e)}")
        raise ValueError(f"An error occurred while create client: [{type_client}]. Error: {str(e)}")

    # Debug: Print response structure
    # print(f"Response choices: {response.choices}")
    # if response.choices:
    #     print(f"First choice message: {response.choices[0].message}")
    #     print(f"Tool calls: {response.choices[0].message.tool_calls}")
    
    # Check if response has standard tool_calls (OpenAI format)
    if response and response.choices and response.choices[0].message.tool_calls:
        arguments = response.choices[0].message.tool_calls[0].function.arguments
        specifications = parse_string_to_dict(arguments)
        return specifications
    
    # Check if response has Groq function call format in content
    if response and response.choices:
        content = response.choices[0].message.content
        func_name, args_str = parse_groq_function_call(content)
        
        if func_name and args_str:
            logger.info(f"Parsed Groq function call: {func_name} with args: {args_str}")
            specifications = parse_string_to_dict(args_str)
            return specifications
        else:
            logger.info(f"LLM responded with text: {content}")
    
    raise ValueError("Invalid response structure or missing tool calls.")


def main():
    # Test 1: Extract search query
    print("=== Test 1: Search Query ===")
    try:
        arguments = extract_info(
            query_user="Tôi muốn đặt tai nghe Sony WH-1000XM5 màu trắng",
            tool_call='order_product',
            prompt_sys=PROMPT_SYSTEM['prompt_extract_order'],
            type_client='groq'
        )
        print("✅ Success!")
        for key, value in arguments.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    dotenv.load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
    main()