# https://qdrant.tech/articles/vector-search-filtering/

import uuid
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import Filter
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from base import BaseRetriever

@dataclass
class QdrantQueryEngine(BaseRetriever):
    url: str
    api_key: str
    index_name: str="qdrant_retriever"
    timeout: int=30
    def __post_init__ (self, 
                       embedder: Embeddings, 
                       documents: Document):
        self.client = QdrantClient(
            url=self.url, 
            api_key=self.api_key,
            timeout=self.timeout
        )
        self.embedder = embedder
        self.documents = documents
        self.sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
        self._create_collection()
        self.vector_store = self.upsert()

    def _create_collection(self):
        self.client.recreate_collection(
            collection_name=self.index_name,
            optimizers_config=models.OptimizersConfigDiff(indexing_threshold=10000),
            hnsw_config=models.HnswConfigDiff(
                m=32,  # Increase the number of edges per node from the default 16 to 32
                ef_construct=200,  # Increase the number of neighbours from the default 100 to 200
            ),
            vectors_config={
                models.VectorParams(
                    size=self.embedder.dimensions,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            }
        )
    def upsert(self):
        vector_store = QdrantVectorStore.from_documents(
            documents=self.documents, 
            embedding=self.embedder, 
            sparse_embedding = self.sparse_embeddings,
            colletion_name=self.index_name,
            retrieval_mode=RetrievalMode.HYBRID,
        )
        return vector_store
    
    def query(self, 
              query: str, 
              top_k: int, 
              filter_search: Dict[str, Any]):

        search_result = self.vector_store.similarity_search_with_score(
            query=query, 
            k=top_k, 
            filter=Filter(
                must=[
                    models.FieldCondition(
                        key="group_product_name", 
                        match=models.MatchValue(value="đèn năng lượng mặt trời"), 
                    ),
                    models.FieldCondition(
                        key="price",
                        range=models.Range(
                            gte=3000000,
                            lte=5000000
                        )
                    )
                ],
            ),
            score_threshold=0.75, 
        )
        return search_result
    
    def _count_data(self):
        return self.client.count(collection_name=self.index_name)
    
    def _delete_collection(self):
        self.client.delete_collection(collection_name=self.index_name)

    def format_output_structure(self, output_qdrant: list):
        outtext = ""
        for index, point in enumerate(output_qdrant):
            point = json.loads(json.dumps(point.dict(), indent=4))
            payload = point['payload']
            outtext +=  f"""
                {index+1}. "id": {payload['product_info_id']},
                "product_name": {payload['product_name']},
                "price": {payload['price']} \n"""
        return outtext

if __name__ == "__main__":
    query = "bán cho tôi Bộ Lưu Trữ Năng Lượng Mặt Trời SUNTEK 12V/25Ah PLUS" 
    engine = QdrantQueryEngine()
    engine.testing(query=query)