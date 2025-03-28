import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from models import create_llm, create_embedder
from agent import agent
from tools import search
from extract_specifications import extract_info
from vectorstore import (ElasticQueryEngine, 
                         QdrantQueryEngine,
                         EnsembleQueryEngine)
from config import AragProduct
from typing import Literal


def respose_chatbot(df: pd.DataFrame, 
                    question: str, 
                    search_type: Literal["elasticsearch", "qdrant", "chroma"]="qdrant", 
                    llm_type: Literal['groq', 'openai']='openai', 
                    model_name: str = "gpt-4o-mini"): 

    tool_result = agent.invoke({"input": question, 
                                "intermediate_steps": []})
    tool_name = tool_result.tool
    print(tool_name)

    llm = create_llm(llm_type=llm_type, 
                     model_name=model_name)
    embedder = create_embedder(embedder_type=llm_type)

    if search_type == 'elasticsearch': 
        search_engine = ElasticQueryEngine(cloud_id=os.getenv("ELASTIC_CLOUD_ID"), 
                                            api_key=os.getenv("ELASTIC_API_KEY"), 
                                            dataframe=df)
    elif search_type == 'qdrant':
        search_engine = QdrantQueryEngine(url=os.getenv("QDRANT_CLOUD_ID"), 
                                           api_key=os.getenv("QDRANT_API_KEY"), 
                                           df=df)
    else: 
        search_engine = EnsembleQueryEngine(embedder=embedder, 
                                            df=df)

    context = ""
    if tool_name == 'search_web': 
        for result in search.invoke({"query": question}):
            context += result['content'] + "\n"
    else: 
        demands =  extract_info(query_user=question, 
                                type_client=llm_type)
        if tool_name == "product_search": 
            context = search_engine.query(demands=demands)
        elif tool_name == 'product_order': 
            context = None
        else: 
            context = None

    prompt =  f"""Trả lời câu hỏi: {question} dựa vào thông tin được cung cấp: 
    context: {context}         
    """

    response = llm.invoke(input=prompt)
    return response.content

def main():
    df = pd.read_excel(AragProduct.DATA_PATH)
    question = "Tôi muốn mua điều hòa Inveter 9000 BTU không"
    response = respose_chatbot(df=df, question=question)
    print(response)

if __name__ == '__main__':
    main()    
