import ast
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import asyncio
from elasticsearch import Elasticsearch
from elasticsearch import AsyncElasticsearch
from extract_specs import extract_info
from utils.utils import parse_specification_range
from utils.config import Config
from prompt import FUNC_CALL_TOOLS, PROMPT_SYSTEM

LIST_GROUP_PRODUCT = Config.LIST_GROUP_NAME

@dataclass
class ElasticQueryEngine:
    dataframe: pd.DataFrame = pd.read_csv(Config.DATA_PATH)
    index_name: str="ecommerece"
    timeout: int=30

    def __post_init__(self):
        self.client = Elasticsearch(
          hosts=[f"http://{Config.ELS_HOST}:{Config.ELS_PORT}"], 
        )
        self.async_client = AsyncElasticsearch(
          hosts=[f"http://{Config.ELS_HOST}:{Config.ELS_PORT}"]
        )

        if not self._index_exists():
            self.upsert()

    def _index_exists(self):
        """Check nếu index tồn tại"""
        try:
            return self.client.indices.exists(index=self.index_name)
        except Exception as e:
            print(f"Error checking index existence: {str(e)}")
            return False

    def _count_data(self):
        try:
            num_data = self.client.count(index=self.index_name)['count']
            return num_data
        except Exception as e:
            print(f"Error counting data: {str(e)}")
            return 0
    
    def upsert(self):
        # mapping data type pandas to els 
        dtype_mapping = {
            'int64': 'integer',
            'float64': 'float',
            'object': 'text' 
        }
        column_mapping = {"properties": 
                          {col: {"type": dtype_mapping[str(dtype)]} 
                           for col, dtype in self.dataframe.dtypes.items()}
        }
        try:
            if not self.client.indices.exists(index=self.index_name):
                self.client.indices.create(index=self.index_name, body={"mappings": column_mapping})
                # Index documents
                for i, row in self.dataframe.iterrows():
                    doc = {col: row[col] for col in row.index}

                    self.client.index(index=self.index_name, id=i, document=doc)

                self.client.indices.refresh(index=self.index_name)

                print("Upsert data to Elastic search client successfull!")
            else:
              print("Index already exists. Skipping upsert.")
        except Exception as e:
            print(f"An error occurred while connecting to Elastic Search: {str(e)}")
            raise ValueError(f"An error occurred while connecting to Elastic Search: {str(e)}")
        
    def create_filter_range(self, field: str, value: str) -> Dict:
        """
        Hàm này tạo ra filter range cho câu query.

        Args:
            - field: tên field cần filter
            - value: giá trị cần filter
        Return:
            - trả về dictionary chứa thông tin filter range
        """
        min_value, max_value = parse_specification_range(value)
        range_filter = {
            "range": {
                field: {
                    "gte": min_value,
                    "lte": max_value
                }
            }
        }
        return range_filter

    def create_elastic_query(
            self,
            top_k: int,
            group_product: str, 
            product_name: str, 
            price: Optional[str] = None,
            power: Optional[str] = None,
            weight: Optional[str] = None,
            volume: Optional[str] = None,) -> Dict:
        query = {
            "query": {
                "bool": {
                    "must": [],
                    "should": [],
                    "filter": []
                }
            },
            "size": top_k
        }

        if group_product: 
            query["query"]["bool"]["must"].append(
                {"match": {"category_name": group_product}}
            )

        if product_name: # nếu có tên sản phẩm
            query["query"]["bool"]["should"] = [
                {"match": {"name": product_name}}
            ]

        for field, value in [('price', price), 
                             ('power', power), 
                             ('weight', weight), 
                             ('volume', volume)]:

            if value:  # Nếu có thông số cần filter
                if "BIGGEST" in value:
                    query["sort"] = [
                        {field: {"order": "desc"}}
                    ]

                elif "SMALLEST" in value:
                    query["sort"] = [
                        {field: {"order": "asc"}}
                    ]

                query['query']['bool']['must'].append(self.create_filter_range(field, value))
        
        # không hỏi thong số -> mặc định search theo sản phẩm bán chạy nhất
        if all(param == '' for param in (power, weight, volume, price)):
            query['sort'] = [
                {"quantity_stock": {"order": "desc"}}
            ]
        return query

    def bulk_search_products(self, queries: List[Dict]) -> List[Dict]:
        """
        Hàm này dùng để search nhiều query trên elasticsearch.

        Args:
            - client: elasticsearch client
            - queries: list chứa các query cần search
        Return:
            - trả về list chứa kết quả search
        """
        body = []
        for query in queries:
            body.extend([{"index": self.index_name}, query])
        
        results = self.client.msearch(body=body)
        return results['responses']

    async def abulk_search_products(self, queries: List[Dict]) -> List[Dict]:
        """
        Async version - search nhiều query trên elasticsearch.

        Args:
            - queries: list chứa các query cần search
        Return:
            - trả về list chứa kết quả search
        """
        body = []
        for query in queries:
            body.extend([{"index": self.index_name}, query])
        
        results = await self.async_client.msearch(body=body)
        return results['responses']


    def query(self, demands: dict)-> Tuple[str, List[Dict], int]:

        """
        Hàm này dùng để search thông tin sản phẩm trên elasticsearch.

        Args:
            - demands: dictionary chứa thông tin cần search
        Returns:
            - trả về câu trả lời, list chứa thông tin sản phẩm, và số lượng sản phẩm tìm thấy
        """
        group_product = demands.get("group", '')

        queries = []
        if group_product in LIST_GROUP_PRODUCT:
            query = self.create_elastic_query(
                demands.get("top_k", 5),
                group_product,
                demands.get("name"), 
                demands.get("price"), 
                demands.get('power'), 
                demands.get('weight'), 
                demands.get('volume')
            )
            queries.append(query)
        else:
            print(f"Group product '{group_product}' not recognized.")        
        
        print("queries: ", queries)
        results = self.bulk_search_products(queries)

        out_text, products_info = "", [] 
        for result in results:
            for i, hit in enumerate(result['hits']['hits']):
                product_details = hit['_source']
                out_text += self._format_output_structure(i, product_details)
                products_info.append({
                    "product_id": product_details['product_id'],
                    "product_name": product_details['name'],
                    "price": product_details['price'],
                    "specification": product_details['specification']
                })
        return out_text, products_info


    def _format_output_structure(self, index: int, product_details: Dict):
        return f"""\n{index + 1}. Tên: '{product_details['name']}' 
        - Mã sản phẩm: {product_details['product_id']} 
        - Giá: {product_details['price']:,.0f} đ
        - Thông số : {product_details['specification']}\n"""
    

    async def aquery(self, demands: dict) -> Tuple[str, List[Dict], int]:
        """
        Async version của query - search thông tin sản phẩm trên elasticsearch.

        Args:
            - demands: dictionary chứa thông tin cần search
        Returns:
            - trả về câu trả lời, list chứa thông tin sản phẩm, và số lượng sản phẩm tìm thấy
        """
        group_product = demands.get("group", '')

        queries = []
        if group_product in LIST_GROUP_PRODUCT:
            query = self.create_elastic_query(
                demands.get("top_k", 5),
                group_product,
                demands.get("name"), 
                demands.get("price"), 
                demands.get('power'), 
                demands.get('weight'), 
                demands.get('volume')
            )
            queries.append(query)
        else:
            print(f"Group product '{group_product}' not recognized.")        
        
        print("queries: ", queries)
        results = await self.abulk_search_products(queries)

        out_text, products_info = "", [] 
        for result in results:
            for i, hit in enumerate(result['hits']['hits']):
                product_details = hit['_source']
                out_text += self._format_output_structure(i, product_details)
                products_info.append({
                    "product_id": product_details['product_id'],
                    "product_name": product_details['name'],
                    "price": product_details['price'],
                    "specification": product_details['specification']
                })
        
        return out_text, products_info
    
    async def close(self):
        """Close async client connections"""
        await self.async_client.close()
    

if __name__ == "__main__":
    retriever = ElasticQueryEngine()
    out_text, product_info = retriever.query({
        "group": "phone",
        "object": "Iphone15",
    })
    import pprint
    pprint.pprint(out_text)