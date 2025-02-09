# https://qdrant.tech/articles/vector-search-filtering/

import uuid
import json
import pandas as pd
from datasets import Dataset
from tqdm import tqdm
from typing import Dict, Any
from dotenv import load_dotenv
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client import models
from dataclasses import dataclass
load_dotenv()

from base import BaseRetriever
from utils import Logger
from config import ArgQdrant


LOGGER = Logger(name=__file__, log_file="qdrant_retriever.log")


@dataclass
class QdrantQueryEngine(BaseRetriever):
    url: str
    api_key: str
    df: pd.DataFrame
    timeout: int=30
    batch_size: int=4
    index_name: str="qdrant_retriever"
    config = ArgQdrant()

    def __post_init__ (self):
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=self.timeout
        )
        self.jina_model = TextEmbedding(model_name="jinaai/jina-embeddings-v2-base-en")
        self.bm25_model = SparseTextEmbedding(model_name="Qdrant/bm25")

        self.create_collection()
        self.upsert()

    def _count_data(self):
        return self.client.count(collection_name=self.index_name).count
    
    def _delete_colection(self):
        self.client.delete_collection(collection_name=self.index_name)
    
    def create_collection(self):
        if not self.client.collection_exists(collection_name=self.index_name):

            self.client.create_collection(
                collection_name=self.index_name,
                optimizers_config=models.OptimizersConfigDiff(indexing_threshold=10000),
                hnsw_config=models.HnswConfigDiff(
                    m=32,  # Increase the number of edges per node from the default 16 to 32
                    ef_construct=200,  # Increase the number of neighbours from the default 100 to 200
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                ),
                vectors_config={
                    "jina-embeddings-v2": models.VectorParams(
                        size=self.config.dimension_vector,
                        distance=models.Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    "bm25": models.SparseVectorParams(
                        modifier=models.Modifier.IDF,
                    )
                }
            )
            LOGGER.log.info(f"Create index name: {self.index_name} successfull!")
        else:
            LOGGER.log.info(f"Collection name: {self.index_name} exists")


    def upsert(self, batch_size: int=4):
        num_data = self._count_data()
        if num_data > 0:
            return
        
        dataset = Dataset.from_pandas(self.df, preserve_index=False)
        for batch in tqdm(dataset.iter(batch_size=batch_size), total=len(dataset) // batch_size):

            dense_embedding = list(self.jina_model.embed(documents=batch['group_name']))
            bm25_embedding = list(self.bm25_model.embed(documents=batch['group_name']))

            self.client.upload_points(
                collection_name=self.index_name,
                points=[
                    models.PointStruct(
                        id=uuid.uuid4().hex,
                        
                        payload={
                            'product_info_id': batch['product_info_id'][i],
                            'group_product_name': batch['group_product_name'][i],
                            'product_name': batch['product_name'][i],
                            'price': batch['lifecare_price'][i],
                            'short_description': batch['short_description'][i],
                            'specifications': batch['specifications'][i],
                            'file_path': batch['file_path'][i],
                            'power': batch['power'][i],
                            'weight': batch['weight'][i],
                            'volume': batch['volume'][i]
                        },
                        vector={
                            "jina-embeddings-v2": dense_embedding[i].tolist(),
                            "bm25": bm25_embedding[i].as_object(),
                        },
                    ) for i, _ in enumerate(batch["group_name"])
                ],
                batch_size=batch_size
            )
        LOGGER.log.info(f"Uploading data to Qdrant client successfull !!")


    def _create_filter_search(self, demands: Dict[str, Any]):
        group_product = demands.get("group")
        filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="group_product_name", 
                    match=models.MatchValue(value=group_product)
                ),
                # models.FieldCondition(
                #     key="price",
                #     range=models.Range(
                #         gte=3000000,
                #         lte=5000000
                #     )
                # )
            ],
        )
        return filter


    def query(self, 
               query: str, 
               demands: dict[str, any] = None):
        
        sparse_embedding = list(self.bm25_model.embed(documents=query))[0]
        dense_embedding = list(self.jina_model.embed(documents=query))[0]

        filter_search = self._create_filter_search(demands=demands)

        search_result = self.client.query_points(
            collection_name=self.index_name,
            prefetch=[
                models.Prefetch(query=sparse_embedding.as_object(), 
                                using="bm25", 
                                limit=self.config.top_k),

                models.Prefetch(query=dense_embedding.tolist(), 
                                using="jina-embeddings-v2", 
                                limit=self.config.top_k),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF), # <--- Combine the scores of the two embeddings
            query_filter=filter_search,
            score_threshold=self.config.score_threshold,
            with_payload=self.config.is_with_payload,
            with_vectors=self.config.is_with_vector,
            limit=self.config.top_k,
        ).points

        response_structured = self.format_output_structure(output_qdrant=search_result)
        return response_structured


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