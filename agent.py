import os
import dotenv
import pandas as pd
from pydantic import BaseModel, Field
from typing import Optional, Dict, Annotated
dotenv.load_dotenv()
from langchain.tools import BaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

def get_product_by_name(product_name: str):
    return product_name

class ProductSearchInput(BaseModel):
    product_name: str = Field(..., description="Tên của sản phẩm dùng để search trong database")

class ProductSearchTool(BaseTool):
    name: Annotated[str, Field(description="Tool name")] = "product_search"
    description: Annotated[str, Field(description="Tool description")] = "Hữu ích khi cần tìm kiếm các thông tin của sản phẩm"
    args_schema: type[BaseModel] = ProductSearchInput

    def _run(self, product_name: str) -> Optional[Dict]:
        return get_product_by_name(product_name)


def get_order(product_name):
    return product_name

class ProductOrderInput(BaseModel):
    product_name: str = Field(..., description="Tên của sản phẩm sử dụng để order")

class ProductOrderTool(BaseTool):
    name: Annotated[str, Field(description="Tool name")] = "product_order"
    description: Annotated[str, Field(description="Tool description")] = "Hữu ích khi khách hàng thảo luận về việc mua bán, giá cả, chốt đơn... sản phẩm"
    args_schema: type[BaseModel] = ProductOrderInput

    def _run(self, product_name: str) -> Optional[Dict]:
        return get_order(product_name)
    

def get_desc():
    return "Chính sách bên em là 1 đổi 1 trong thời gian bảo hành"

class GeneralInfoTool(BaseTool):
    name: Annotated[str, Field(description="Tool name")] = "general_info"
    description: Annotated[str, Field(description="Tool description")] = "Hữu ích khi khách hàng muốn hỏi các thông tin như: chính sách bảo hành, điều khoản, thời gian vận chuyển..."

    def _run(self) -> Optional[Dict]:
        return get_desc()
    
search = TavilySearchResults(max_results=2)


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

agent = create_openai_functions_agent(
    llm=model,
    tools=[ProductOrderTool(), ProductSearchTool(), GeneralInfoTool(), search],
    prompt=prompt,
)

agent_excutor = AgentExecutor(
    agent=agent,
    tools=[ProductOrderTool(), ProductSearchTool(), GeneralInfoTool(), search],
)

question = "Giảm giá sản phẩm điều hòa còn 10 triệu được không ?"

print(agent.invoke({"input": question, "intermediate_steps": []}))
results = agent_excutor.invoke({
    "input": question,
})

print(results)