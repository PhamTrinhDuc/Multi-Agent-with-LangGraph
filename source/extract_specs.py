import os
import dotenv
from openai import OpenAI
from groq import Groq
from typing import Literal
from utils.utils import parse_string_to_dict
from utils.config import Config
from prompt import PROMPT_SYSTEM, FUNC_CALL_TOOLS


def extract_info(query_user: str,
                 tools_calling: list[dict]=FUNC_CALL_TOOLS,
                 prompt_sys: str=PROMPT_SYSTEM['prompt_extract_spec'],
                 type_client: Literal["groq", 'openai']="groq"):
    
    messages = [
        {'role': 'system', 'content': prompt_sys},
        {"role": "user", "content": query_user}]

    response = None
    try:
        if type_client == 'groq':
            client = Groq()
            response = client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=messages,
                tools=tools_calling,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )

        elif type_client == 'openai':
            client = OpenAI()
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=messages,
                tools=tools_calling,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )

        else: 
            raise ValueError(f"No support model: {type_client}")
    except Exception as e:
        print(f"An error occurred while create client: [{type_client}]. Error: {str(e)}")
        raise ValueError(f"An error occurred while create client: [{type_client}]. Error: {str(e)}")

    # Check if response exists and has the expected structure before accessing it
    if response and response.choices and response.choices[0].message.tool_calls:
        arguments = response.choices[0].message.tool_calls[0].function.arguments
        specifications = parse_string_to_dict(arguments)
        return specifications
    else:
        raise ValueError("Invalid response structure or missing tool calls.")


def main():
    # Test 1: Extract search query
    print("=== Test 1: Search Query ===")
    try:
        arguments = extract_info(
            query_user="Tôi muốn mua Laptop Dell từ 15 đến 20 triệu",
            # prompt_sys=PROMPT_SYSTEM['prompt_extract_spec'],
            prompt_sys=PROMPT_SYSTEM['prompt_extract_compare'],
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