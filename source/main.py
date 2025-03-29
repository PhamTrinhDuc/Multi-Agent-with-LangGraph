import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from models import create_llm, create_embedder
from agent import agent
from tools import search
from extract_specifications import extract_info
from vectorstore import ChromaQueryEngine
from config import AragProduct
from typing import Literal


def respose_chatbot(df: pd.DataFrame, 
                    question: str, 
                    llm_type: Literal['groq', 'openai']='openai', 
                    model_name: str = "gpt-4o-mini"): 

    llm = create_llm(llm_type=llm_type, 
                     model_name=model_name)
    embedder = create_embedder(embedder_type=llm_type)

    search_engine = ChromaQueryEngine(embedder=embedder, 
                                            df=df)
    demands =  extract_info(query_user=question, 
                                type_client=llm_type)
    context = search_engine.query(demands=demands)

    prompt =  f"""Trả lời câu hỏi: {question} dựa vào thông tin được cung cấp: 
    context: {context}         
    """
    response = llm.invoke(input=prompt)
    return response.content

def main():
    df = pd.read_excel(AragProduct.DATA_PATH)
    question = "Tôi muốn mua điện thoại"
    response = respose_chatbot(df=df, question=question)
    print(response)

if __name__ == '__main__':
    main()    
