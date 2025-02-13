from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_community.callbacks.manager import get_openai_callback
from langchain_community.cache import SQLiteCache
from typing import Literal, Dict
from config import AragProduct
import langchain 

langchain.llm_cache = SQLiteCache(database_path=AragProduct.CACHE_PATH)


def create_llm(llm_type: Literal['groq', 'openai'], model_name: str):
    
    if llm_type == 'openai':
        llm = ChatOpenAI(model=model_name)
    else:
        llm = ChatGroq(model=model_name)

    return llm


def create_embedder(embedder_type: Literal['openai']):
    if embedder_type == 'openai': 
        embedder = OpenAIEmbeddings(model="text-embedding_ada-002")
        return embedder