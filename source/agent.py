import os
import dotenv
dotenv.load_dotenv()
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_functions_agent
from tools import (
    ProductOrderTool,
    ProductSearchTool,
    GeneralInfoTool,
    search,
)
from models import create_llm


system_message = "Bạn là 1 chatbot bán hàng hữu ích. Hãy dựa vào câu hỏi của người dùng để trả lời."
prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

model = create_llm(llm_type="openai")

tools=[ProductSearchTool(), ProductOrderTool(), GeneralInfoTool(), search]

agent = create_openai_functions_agent(
    llm=model,
    tools=tools,
    prompt=prompt,
)

