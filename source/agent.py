import os
import dotenv
import pandas as pd
dotenv.load_dotenv()
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from tools import (
    ProductOrderTool,
    ProductSearchTool,
    GeneralInfoTool,
    search,
)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


system_message = "Bạn là 1 chatbot bán hàng hữu ích. Hãy dựa vào câu hỏi của người dùng để trả lời."
prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

model = ChatOpenAI(
    temperature=0.5, 
    streaming=True, 
    model="gpt-4o-mini",
)

tools=[ProductSearchTool(), ProductOrderTool(), GeneralInfoTool(), search]

agent = create_openai_functions_agent(
    llm=model,
    tools=tools,
    prompt=prompt,
)

