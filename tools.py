import os
import dotenv
from pydantic import BaseModel
from pydantic import Field
from typing import Annotated
dotenv.load_dotenv()
from langchain.tools import BaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
from prompt import PROMPT_TOOLS

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

class ProductSearchTool(BaseTool):
    name: Annotated[str, Field(description="Tool name")] = "product_search"
    description: Annotated[str, Field(description="Tool description")] = PROMPT_TOOLS['search_product']
    def _run(self):
        pass


class ProductOrderTool(BaseTool):
    name: Annotated[str, Field(description="Tool name")] = "product_order"
    description: Annotated[str, Field(description="Tool description")] = PROMPT_TOOLS['order']
    def _run(self):
        pass


class GeneralInfoTool(BaseTool):
    name: Annotated[str, Field(description="Tool name")] = "general_info_search"
    description: Annotated[str, Field(description="Tool description",)] = PROMPT_TOOLS['general_info']
    def _run(self):
        pass


search = TavilySearchResults(
    name="search_web", 
    description = PROMPT_TOOLS['search_web'], 
    max_results=3, 
    return_direct=True
)
