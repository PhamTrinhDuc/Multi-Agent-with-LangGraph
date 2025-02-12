import os
import pandas as pd
from uuid import uuid4
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings

from base import BaseRetriever
from utils import Logger
from config import ArgChroma

LOGGER = Logger(name=__file__, log_file="chroma_retriever.log")

@dataclass
class EnsembleQueryEngine(BaseRetriever):
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
            embedding_function=self.embedder, 
            persist_directory=self.config.db_persist_path
        )
        self.documents = self.upsert()

    def upsert(self):
        documents = []
        for _, row in self.df.iterrows():
            content = (
                f"Tên sản phẩm: '{row['product_name']}'\n"
                f"Mã sản phẩm: {row['product_info_id']}\n"
                f"Giá: {row['lifecare_price']}\n"
                f"Thông số kỹ thuật: {row['specifications']}\n"
            )
            metadata = {col: row[col] for col in row.index} 
            documents.append(Document(page_content=content, metadata=metadata))
        
        ids = [str(uuid4()) for _ in range(len(documents))]
        
        if not os.path.exists(self.config.db_persist_path):
            return self.client.from_documents(
                ids=ids,
                documents=documents,
                embedding=self.embeder,
                persist_directory=self.config.db_persist_path
            )
        LOGGER.log.info(msg="Upsert data to vector db successfull!")
        return documents
    

    def _create_bm25_retriever(self) -> BM25Retriever:
        """Create BM25 retriever"""
        retriever = BM25Retriever.from_documents(self.documents)
        retriever.k = self.config.top_k
        return retriever
    
    def _create_mmr_retriever(self, filter_search: Dict[str, Any]=None) -> Chroma: 
        """
        top_k: Amount of documents to return (Default: 3)
        fetch_k: Amount of documents to pass to MMR algorithm (Default: 15)
        lambda_mult: Diversity of results returned by MMR; 
            1 for minimum diversity and 0 for maximum. (Default: 0.25)
        filter: Filter by document metadata

        >>> examples:  
            default: search_kwargs = {'k': 3, 'lambda_mult': 0.25, 'fetch_k': 15}
            custom: search_kwargs = {'k': 3, 'lambda_mult': 0.25, 'filter': {"product_name": "Dieu_hoa"}}
        """
        
        filter_default = {'k': self.config.top_k, 
                          'lambda_mult': self.config.lambda_mult, 
                          'fetch_k': self.config.fetch_k}
        if filter_search is not None:
            filter_default['filter'] = filter_search

        return self.client.as_retriever(
            search_type="mmr",
            search_kwargs=filter_default
        )
    
    def _create_vanilla_retriever(self, filter_search: Dict[str, Any]=None) -> Chroma:
        """
        Create vanilla vector similarity retriever
        top_k: Amount of documents to return (Default: 3)
        score_threshold: Minimum relevance threshold for similarity_score_threshold
        filter search: Filter by document metadata

        >>> examples:  
            default: search_kwargs = {'k': 3, 'score_threshold': 0.6}
            custom: search_kwargs = {'k': 3, 'score_threshold': 0.25, 'filter': {"product_name": "Dieu_hoa"}}
        """
        filter_default = {'k': self.config.top_k, 
                          'score_threshold': self.config.score_threshold}
        
        if filter_search is not None:
            filter_default['filter'] = filter_search

        return self.client.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=filter_default
        )
    
    def _build_ensemble_retriever(self, filter_search: Dict[str, Any]=None,):
        """
        FOR MMR ALGORITHM: 
            fetch_k: Amount of documents to pass to MMR algorithm (Default: 15)
            lambda_mult: Diversity of results returned by MMR; 
                1 for minimum diversity and 0 for maximum. (Default: 0.25)
        FOR SIMILAR ALGORITHM: 
            score_threshold: Minimum relevance threshold for similarity_score_threshold
        
        weights_ensemble: weights for each search type [similarity, bm25, mmr]
        top_k: Amount of documents to return (Default: 3)
        filter_search: Filter by document metadata
        """
        bm25_retriever = self._create_bm25_retriever()

        # vanilla_retriever = self._create_vanilla_retriever(top_k=top_k,
        #                                                    score_threshold=score_threshold,
        #                                                    filter_search=filter_search)
        mmr_retriever = self._create_mmr_retriever(filter_search=filter_search)

        ensemble_retriever=  EnsembleRetriever(
            retrievers=[ bm25_retriever, mmr_retriever],
            weights=self.config.weights_ensemble
        )
        return ensemble_retriever
    

    def _create_filter_search(self, demands: Dict[str, Any]):
        filter = {
            "group_product_name": demands['group']
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

        retriever = self._build_ensemble_retriever(filter_search=filter_search)
        LOGGER.log.info("Create ensemble retriever successfull!")

        contents = retriever.invoke(input=query)
        return "\n".join(doc.page_content for doc in contents)

    def _drop_db(self, path_db: str):
        os.remove(path=path_db)