import dotenv
from typing import List, Dict, Any
from collections import defaultdict
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
dotenv.load_dotenv()

from base import BaseVectorStorage

class ChromaQueryEngine(BaseVectorStorage):
    def __init__(self, 
                 embeder: Embeddings, 
                 documents: Document, 
                 weights_ensemble: List[int],
                 filter_search: Dict[str, Any]=None, 
                 db_persist_path: str="./data/chroma_db", 
                 top_k: int=3):
        
        super().__init__()
        self.embeder = embeder
        self.documents = documents
        self.weights_ensemble = weights_ensemble
        self.filter_demands = filter_search or {"k": top_k}
        self.db_persist_path = db_persist_path
        self.top_k = top_k

        self.vector_db = self.upsert()

    def upsert(self):
        if not self.db_persist_path:
            return Chroma.from_documents(
                documents=self.documents,
                embedding=self.embeder,
                persist_directory=self.db_persist_path
            )
        return Chroma(
            embedding_function=self.embeder, 
            persist_directory=self.db_persist_path
        )

    def _create_mmr_retriever(self) -> Chroma: 
        "Create MMR retriever"
        # filter = {"price": {"$gte": 0}, "price": {"$lte": 1000000000}}
        # for key, value in demands.items():

        #     if value and key in ["price", "power", "weight", "volume"]:
        #         min_val, max_val = RetrieveHelper().parse_specification_range(specification=value)
        #         filter =  [{key: {"$gte": min_val}, key: {"$lte": max_val}}]
        #         if key == 'price': break
        return self.vector_db.as_retriever(
            search_type="mmr",
            search_kwargs=self.filter_search
        )
    def _create_bm25_retriever(self) -> BM25Retriever:
        """Create BM25 retriever"""
        retriever = BM25Retriever.from_documents(self.documents)
        retriever.k = self.top_k
        return retriever
    
    def _create_vanilla_retriever(self) -> Chroma:
        """Create vanilla vector similarity retriever"""

        return self.vector_db.as_retriever(
            search_type="similarity",
            search_kwargs=self.filter_search
            )
    
    def _build_ensemble_retriever(self):
        bm25_retriever = self._create_bm25_retriever()
        vanilla_retriever = self._create_vanilla_retriever()
        mmr_retriever = self._create_mmr_retriever()

        ensemble_retriever=  EnsembleRetriever(
            retrievers=[vanilla_retriever, bm25_retriever, mmr_retriever],
            weights=self.weights_ensemble
        )
        return ensemble_retriever
    
    def query(self, query: str):
        """
        Get relevant context for a query about a specific product
        
        Args:
            query: User query after rewriting
            product_name: Name of the product to search in
            
        Returns:
            Relevant context for the query
        """
        retriever = self.retriever_builder.build_ensemble_retriever()
        contents = retriever.invoke(input=query)
        return "\n".join(doc.page_content for doc in contents)


def main():
    pass

if __name__ == "__main__":
    main()