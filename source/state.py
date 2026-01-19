from langgraph.graph.message import add_messages
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from typing import TypedDict, Annotated, Union

class SearchState(TypedDict): 
  question: HumanMessage
  context: str
  messages: Annotated[list, add_messages]

class CompareState(TypedDict): 
  question: HumanMessage
  group: str
  product_1: str
  product_2: str
  messages: Annotated[list, add_messages]
  comparison_result: Union[dict, str]

class OrderState(TypedDict): 
  question: HumanMessage
  product_id: str
  quantity: int
  order_status: str
  messages: Annotated[list, add_messages]

class MainState(TypedDict): 
  question: HumanMessage
  messages: Annotated[list, add_messages]
  next_action: str

