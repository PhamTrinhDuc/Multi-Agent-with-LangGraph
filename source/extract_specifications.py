import os
import dotenv
from openai import OpenAI
from groq import Groq
from typing import Literal
from utils import parse_string_to_dict, Logger
from prompt import PROMPT_SYSTEM, FUNC_CALL_TOOLS

dotenv.load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")


LOGGER = Logger(name=__file__, log_file="extract_query.log")


def extract_info(query_user: str,
                 tools_calling: list[dict]=FUNC_CALL_TOOLS,
                 prompt_sys: str=PROMPT_SYSTEM['extract_query'],
                 type_client: Literal["groq", 'openai']="groq"):
    
    messages = [
        {'role': 'system', 'content': prompt_sys},
        {"role": "user", "content": query_user}]

    try:
        if type_client == 'groq':
            client = Groq()
            response = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=messages,
                tools=tools_calling,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )

        else:
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools_calling,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )

    except Exception as e:
        LOGGER.log.error(f"An error occurred while create client: [{type_client}]. Error: {str(e)}")

    arguments = response.choices[0].message.tool_calls[0].function.arguments
    
    specifications = parse_string_to_dict(arguments)
    return specifications


def main():
    arguments = extract_info("Tôi muốn mua điều hòa từ 10 đến 12 triệu")
    for key, value in arguments.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()