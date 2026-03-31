import os
import pandas as pd
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv("/home/ducpham/workspace/Multi-Agent-with-LangGraph/source/.env")

@dataclass
class Config:
    DATA_PATH: str = "/home/ducpham/workspace/Multi-Agent-with-LangGraph/product_variant.csv"
    LIST_GROUP_NAME = pd.unique(pd.read_csv(DATA_PATH)['category_name'].tolist())

    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_MODEL: str = "gpt-4o-mini"

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")   
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    ELS_HOST: str = os.getenv("ELS_HOST", "localhost")
    ELS_PORT: int = int(os.getenv("ELS_PORT", 9200))