import threading
from typing import Optional, Literal
from loguru import logger
from langchain.tools import BaseTool
from retriever.els import ElasticQueryEngine
from extract_specs import extract_info
from prompt import PROMPT_SYSTEM

class RetrieverTool(BaseTool):
    name: str = "Search_Product"

    description: str = """
    Sử dụng tool để này để tìm kiếm sản phẩm thông tin sản phẩm từ câu hỏi của người dùng. Trong các trường hợp: 
    - Khi người dùng muốn tìm kiếm thông tin sản phẩm
    - Khi người dùng muốn đặt hàng sản phẩm, nếu có thông tin sản phẩm rồi thì bỏ qua bước tìm kiếm
    - Khi người dùng muốn so sánh sản phẩm với sản phẩm
    """

    class Config:
        extra = "allow"  # Allow adding new attributes after init

    def __init__(
        self,
        tool_call: Literal["search_products", "compare_products", "order_product"],
        client: str = "groq", 
        top_k: int = 1,
    ):
        super().__init__()

        self._retriever = None
        self.tool_call = tool_call
        self.client = client
        self.top_k = top_k

    @property
    def retriever(self):
        if not self._retriever:
            with threading.Lock():
                self._retriever = ElasticQueryEngine()
        return self._retriever

    def _extract_query(self, query: str) -> str:
      demands = extract_info(
        query_user=query,
        tool_call=self.tool_call,
        prompt_sys=PROMPT_SYSTEM['prompt_extract_order'],
        type_client=self.client
      )
      demands = {**demands, "top_k": self.top_k, "name": demands.get('product', '')}
      return demands
    
    def _run(self, query: str) -> str:
        try:
            demands = self._extract_query(query)
            # Perform hybrid search
            results = self.retriever.query(demands=demands)
            return results

        except Exception as e:
            error_msg = f"Error retrieving Product information: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def _arun(self, query: str) -> str:
      try:
          demands = self._extract_query(query)
          # Perform async hybrid search
          results = await self.retriever.aquery(demands=demands)
          return results

      except Exception as e:
          error_msg = f"Async error retrieving Product information: {str(e)}"
          logger.error(error_msg)
          raise ValueError(error_msg)


if __name__ == "__main__":
    # python -m tools.retriever_tool

    tool = RetrieverTool(top_k=2)
    query = "Tôi muốn đặt hàng một chiếc điện thoại iPhone 13 Pro Max màu xanh dương, dung lượng 256GB"
    response = tool.invoke(input=query)
    print(f"Query: {query}\n")
    import pprint
    pprint.pprint(response)