
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from base import BaseVectorStorage


class MongoDBRetriever(BaseVectorStorage):
    def __init__(self, 
                 mongodb_uri: str,
                 db_name: str="mongodb",
                 collection_name: str="mongo_agent",
                 index_name: str="vector_index"):
        
        super().__init__()
        client = MongoClient(mongodb_uri, appname="devrel.content.python")
    
    def upsert(self, data):
        return super().upsert(data)
    
    def query(self, query, top_k):
        return super().query(query, top_k)