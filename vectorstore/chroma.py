import os
import dotenv
from chromadb import Client
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
dotenv.load_dotenv()

from base import BaseRetriever

class EnsembleQueryEngine(BaseRetriever):
    _COLLECTION_NAME_ = "chroma_ensemble"
    def __init__(self, 
                 embedder: Embeddings, 
                 documents: Document, 
                 weights_ensemble: List[float],
                 db_persist_path: str="./data/chroma_db"):
        """
        Args: 
            embedder: embedding model 
            documents: excel data convert to Document 
            weights_ensemble: weights for each search type [similarity, bm25, mmr]
            db_persist_path: db storage directory

        """
        super().__init__()
        self.embeder = embedder
        self.documents = documents
        self.weights_ensemble = weights_ensemble
        self.db_persist_path = db_persist_path

        self.client = Chroma(
            collection_name=self._COLLECTION_NAME_, 
            embedding_function=embedder, 
            persist_directory=db_persist_path
        )
        self.upsert()

    def upsert(self):
        if not os.path.exists(self.db_persist_path):
            return self.client.from_documents(
                collection_name=self._COLLECTION_NAME_,
                documents=self.documents,
                embedding=self.embeder,
                persist_directory=self.db_persist_path
            )

    def _create_bm25_retriever(self, top_k: int=3) -> BM25Retriever:
        """Create BM25 retriever"""
        retriever = BM25Retriever.from_documents(self.documents)
        retriever.k = top_k
        return retriever
    
    def _create_mmr_retriever(self, 
                              top_k: int=3, 
                              lambda_mult: float=0.25, 
                              fetch_k: int=15, 
                              filter_search: Dict[str, Any]=None) -> Chroma: 
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
        

        filter_default = {'k': top_k, 'lambda_mult': lambda_mult, 'fetch_k': fetch_k}
        if filter_search is not None:
            filter_default['filter'] = filter_search

        return self.client.as_retriever(
            search_type="mmr",
            search_kwargs=filter_default
        )
    
    def _create_vanilla_retriever(self, 
                                  top_k: int=3,
                                  score_threshold: float=0.75,
                                  filter_search: Dict[str, Any]=None) -> Chroma:
        """
        Create vanilla vector similarity retriever
        top_k: Amount of documents to return (Default: 3)
        score_threshold: Minimum relevance threshold for similarity_score_threshold
        filter search: Filter by document metadata

        >>> examples:  
            default: search_kwargs = {'k': 3, 'score_threshold': 0.75}
            custom: search_kwargs = {'k': 3, 'score_threshold': 0.25, 'filter': {"product_name": "Dieu_hoa"}}
        """
        filter_default = {'k': top_k, 'score_threshold': score_threshold}
        if filter_search is not None:
            filter_default['filter'] = filter_search

        return self.client.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=filter_default
        )
    
    def _build_ensemble_retriever(self, 
                                  filter_search: Dict[str, Any]=None,
                                  top_k: int=3,
                                  score_threshold: float=0.75,
                                  lambda_mult: float=0.25, 
                                  fetch_k: int=15):
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
        bm25_retriever = self._create_bm25_retriever(top_k=top_k)

        vanilla_retriever = self._create_vanilla_retriever(top_k=top_k,
                                                           score_threshold=score_threshold,
                                                           filter_search=filter_search)
        
        mmr_retriever = self._create_mmr_retriever(top_k=top_k, 
                                                   fetch_k=fetch_k,
                                                   lambda_mult=lambda_mult,
                                                   filter_search=filter_search)

        ensemble_retriever=  EnsembleRetriever(
            retrievers=[vanilla_retriever, bm25_retriever, mmr_retriever],
            weights=self.weights_ensemble
        )
        return ensemble_retriever
    
    def query(self, 
              query: str, 
              filter_search: Dict[str, Any]=None,
              **params_search):
        """
        Get relevant context for a query about a specific product
        
        Args:
            query: User query after rewriting
            product_name: Name of the product to search in
            
        Returns:
            Relevant context for the query
        """

        retriever = self._build_ensemble_retriever(filter_search=filter_search, 
                                                  **params_search)
        contents = retriever.invoke(input=query)
        return "\n".join(doc.page_content for doc in contents)

def main():
    retriever = EnsembleQueryEngine(embedder=, documents=, weights_ensemble=, db_persist_path=)
    response = retriever.query(query=, filter_search=, **params_search)
    print(response)


if __name__ == "__main__":
    main()