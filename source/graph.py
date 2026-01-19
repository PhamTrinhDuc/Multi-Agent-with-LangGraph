import os
import sqlite3
from state import MainState, SearchState, CompareState, OrderState
from models import RouterDecision, ValidateContextOutput, ComparisonResult
from langchain_groq import ChatGroq
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages.utils import (trim_messages, count_tokens_approximately)
from langchain.agents import create_agent
from langgraph.graph import START, END, StateGraph
from langgraph.store.sqlite import SqliteStore
from langgraph.checkpoint.sqlite import SqliteSaver
from utils.config import Config
from extract_specs import extract_info
from retriever import ElasticQueryEngine
from prompt import FUNC_CALL_TOOLS, PROMPT_SYSTEM


db_path = "./ecommerce.db"
conn = sqlite3.connect(db_path, check_same_thread=False)

llm = ChatGroq(model=Config.GROQ_MODEL, api_key=Config.GROQ_API_KEY)
retriever = ElasticQueryEngine()


class SearchSubGraph: 
  def __init__(self): 
    self.retriever = retriever
    self.llm_structured = llm.with_structured_output(ValidateContextOutput)
  
  def search_node(self, state: SearchState): 
    demands = extract_info(query_user=state['question'].content, type_client='openai')
    out_text, _ = self.retriever.query(demands=demands)
    return {"context": out_text}
  
  def responder_node(self, state: SearchState): 
    question = state['question'].content
    context = state['context']
    
    messages = [
      {
        'role': 'system',
        'content': PROMPT_SYSTEM['prompt_sys']
      },
      {
        'role': 'user',
        'content':f"""Câu hỏi của khách hàng: {question}.
                  Phần nội dung có thể liên quan đến câu hỏi: {context}
                  """
      }
    ]
    response = llm.invoke(input=messages)
    return {"messages": [response]}
  
  def init_subgraph(self): 
    graph = StateGraph(SearchState)

    graph.add_node("searcher", self.search_node)
    graph.add_node("responder", self.responder_node
                   )
    graph.set_entry_point("searcher")
    graph.add_edge("searcher", "responder")
    graph.add_edge("responder", END)

    return graph.compile()
  

class CompareSubGraph: 
  def __init__(self): 
    self.llm = llm.with_structured_output(ComparisonResult)

  def extract_product_node(self, state: CompareState): 
    """Trích xuất thông tin sản phẩm từ câu hỏi"""
    question = state['question'].content
    try: 
      extracted_info = extract_info(query_user=question,
                                    type_client='groq', 
                                    prompt_sys=PROMPT_SYSTEM['prompt_extract_compare']
                                    )
      return {**extracted_info}
    except Exception as e:
      print(f"Error extracting product info: {str(e)}")
      raise ValueError(f"Failed to extract product information. {str(e)}")

  def compare_node(self, state: CompareState):
    """So sánh 2 sản phẩm"""
    product_1 = state.get('product_1', '')
    product_2 = state.get('product_2', '')
    group = state.get('group', '')

    demands1 = {"name": product_1, "group": group, 'top_k': 2}
    demands2 = {"name": product_2, "group": group, 'top_k': 2}
    try:
      product1 = retriever.query(demands=demands1)
      product2 = retriever.query(demands=demands2)

      messages = [
        {
          'role': 'system',
          'content': PROMPT_SYSTEM['prompt_compare']
        },
        {
          'role': 'user',
          'content': f"""
          Sản phẩm 1: {product1[1]}\n Sản phẩm 2: {product2[1]}
          """
        }
      ]

      response = self.llm.invoke(input=messages)
      formated_comparison =str({
        "comparison_table": response.comparison_table,
        "recommendation": response.recommendation
      })
      return {
        'messages': [AIMessage(content=formated_comparison)]
      }
    
    except Exception as e:
      print(f"Error comparing products: {str(e)}")
      return {
        'messages': [f"Lỗi trong quá trình so sánh sản phẩm: {str(e)}"]
      }

  def init_subgraph(self): 
    graph = StateGraph(CompareState)

    graph.add_node("extractor", self.extract_product_node)
    graph.add_node("compare", self.compare_node)

    graph.set_entry_point("extractor")
    graph.add_edge("extractor", "compare")
    graph.add_edge("compare", END)
    
    return graph.compile()


class OrderSubGraph: 
  def __init__(self): 
    pass
  
  def order_node(self, state: OrderState): 
    """Node đặt hàng - placeholder"""
    return {"messages": ["Đơn hàng đã được tạo thành công!"]}
  
  def init_subgraph(self):
    graph = StateGraph(OrderState)

    graph.add_node("orderer", self.order_node)
    graph.set_entry_point("orderer")
    graph.add_edge("orderer", END)    
    return graph.compile()


class GraphEcommerce: 
  def __init__(self): 
    self.search_subgraph = SearchSubGraph().init_subgraph()
    self.compare_subgraph = CompareSubGraph().init_subgraph()
    self.order_subgraph = OrderSubGraph().init_subgraph()
    self.memory = SqliteSaver(conn=conn)
    self.store = SqliteStore(conn=conn)
    self.llm_structured = llm.with_structured_output(RouterDecision)


  def trim_messages_node(self, state: MainState): 
    print("Trimming messages...")
    trimmed_messages = trim_messages(
      messages=state['messages'],
      max_tokens=2048, 
      token_counter=count_tokens_approximately,
      # start_on="human", 
      # end_on=("human", "tool")
    )
    return {"messages": trimmed_messages}

  def supervisor_node(self, state: MainState): 
    question = state['question'].content
    history = [{'role': msg.type, 'content': msg.content} for msg in state['messages']]
    print("History for router:", history[0])

    messages = [
      {
        'role': 'system', 
        'content': PROMPT_SYSTEM['prompt_router'].format(history=history)
      },
      {
        'role': 'user', 
        'content': question
      }
    ]
    
    response = self.llm_structured.invoke(input=messages)
    print("Question after router rewrite:", response.question)
    return {"next_action": response.next_action, 'question': HumanMessage(response.question)}

  def condition_router(self, state: MainState): 
    return state['next_action']

  def init_graph(self): 
    graph = StateGraph(MainState)

    graph.add_node("trim_messages", self.trim_messages_node)
    graph.add_node("supervisor", self.supervisor_node)
    graph.add_node("searcher", self.search_subgraph)
    graph.add_node("orderer", self.order_subgraph)
    graph.add_node("comparer", self.compare_subgraph)

    graph.set_entry_point("trim_messages")
    graph.add_edge("trim_messages", "supervisor")
    graph.add_conditional_edges(
      "supervisor",
      self.condition_router,
      {
        "search": "searcher",
        "order": "orderer",
        "compare": "comparer"
      }
    )
    
    graph.add_edge("searcher", END)
    graph.add_edge("orderer", END)
    graph.add_edge("comparer", END)
    
    app = graph.compile(checkpointer=self.memory, store=self.store)
    return app


def main(): 
  graph = GraphEcommerce().init_graph()
  png_image = graph.get_graph().draw_mermaid_png()
  with open("graph.png", "wb") as f:
    f.write(png_image)

  # graph = SearchSubGraph().init_subgraph()
  # config = {"configurable": {"thread_id": "subgraph_001"}}
  # init_input = {
  #   # "question": HumanMessage("Bên bạn có tai nghe không?"),
  #   "question": HumanMessage("So sánh cái Sony với cái Apple đi")
  # }
  # result = graph.invoke(init_input, config=config)
  # print("Final Result:", result)


if __name__ == "__main__": 
  main()


# References:
# https://deepwiki.com/langchain-ai/langchain-academy/5.3-external-memory-with-sqlitesaver