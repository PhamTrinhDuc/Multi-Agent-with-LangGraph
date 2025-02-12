from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.cache import SQLiteCache
from typing import Literal, Dict
from config import AragProduct
import langchain 

langchain.llm_cache = SQLiteCache(database_path=AragProduct.CACHE_PATH)


def create_llm(llm_type: Literal['groq', 'openai']):
    
    if llm_type == 'openai':
        llm = ChatOpenAI(model="gpt-4o-mini")
    else:
        llm = ChatGroq(model="llama-3.3-70b-specdec")

    return llm
