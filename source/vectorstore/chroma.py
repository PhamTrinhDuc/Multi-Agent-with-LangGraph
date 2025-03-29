import os
import pandas as pd
from uuid import uuid4
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from langchain_core.embeddings import Embeddings

from source.base import BaseRetriever
from source.utils import Logger
from source.config import ArgChroma

LOGGER = Logger(name=__file__, log_file="chroma_retriever.log")

@dataclass
class ChromaQueryEngine(BaseRetriever):
    embedder: Embeddings 
    df: pd.DataFrame
    config = ArgChroma()

    def __post_init__(self):
        """
        Args: 
            embedder: embedding model 
            df: dataframe 
            weights_ensemble: weights for each search type [similarity, bm25, mmr]
            db_persist_path: db storage directory

        """

        self.client = Chroma(
            collection_name=self.config.collection_name,
            embedding_function=self.embedder, 
            persist_directory=self.config.db_persist_path
        )
        self.upsert()

    def upsert(self):
        documents = []
        for _, row in self.df.iterrows():
            content = (
                f"Tên sản phẩm: '{row['name']}'\n"
                f"Giá: {row['price']}\n"
                f"Thông số kỹ thuật: {row['specification']}\n"
                f"Đặc điểm nổi bật: {row['description']}\n"
            )
            metadata = {col: row[col] for col in row.index if col not in ['name', 'price', 'specification', 'description', 'created_at', 'updated_at']} 
            documents.append(Document(page_content=content, metadata=metadata))
        
        ids = [str(uuid4()) for _ in range(len(documents))]
        
        if len(os.listdir(self.config.db_persist_path)) < 2:
            self.client.add_documents(documents=documents, ids=ids)
            LOGGER.log.info(msg="Upsert data to vector db successfull!")
        return documents
    


    def _create_filter_search(self, demands: Dict[str, Any]):
        filter = {
            "category_name": demands['group']
        }
        return filter

    def query(self, 
              query: str, 
              demands: Dict[str, Any]=None):
        """
        Get relevant context for a query about a specific product
        
        Args:
            query: User query after rewriting
            product_name: Name of the product to search in
            
        Returns:
            Relevant context for the query
        """
        filter_search = None
        if demands is not None:
            filter_search = self._create_filter_search(demands=demands)

        results = self.client.similarity_search(
            query=query,
            k=self.config.top_k,
            filter=filter_search,
        )
        # for res in results:
        #     print(f"* {res.page_content} [{res.metadata}]")

        return "\n".join(doc.page_content for doc in results)

    def _drop_db(self, path_db: str):
        os.remove(path=path_db)