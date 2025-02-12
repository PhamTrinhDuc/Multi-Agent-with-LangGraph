import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from models import create_llm
from agent import agent
from tools import search
from extract_specifications import extract_info
from vectorstore import ElasticQueryEngine
from config import AragProduct

question = "bán cho tôi điều hòa khoảng 10 triệu"
df = pd.read_excel(AragProduct.DATA_PATH)

tool_result = agent.invoke({"input": question, "intermediate_steps": []})
tool = tool_result.tool

demands = extract_info(query_user=question)

llm = create_llm(llm_type="openai")
search_product = ElasticQueryEngine(cloud_id=os.getenv("ELASTIC_CLOUD_ID"), 
                                    api_key=os.getenv("ELASTIC_API_KEY"), 
                                    dataframe=df)

context = ""

if tool == 'search_web': 
    for result in search.invoke({"query": question}):
        context += result['content'] + "\n"
    
elif tool == "product_search": 
    context = search_product.query(demands=demands)


prompt =  f"""Trả lời câu hỏi: {question} dựa vào thông tin được cung cấp: 
context: {context}         
"""

print(prompt)

response = llm.invoke(input=prompt)
print(response.content)
