import ast
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from elasticsearch import Elasticsearch
from source.base import BaseRetriever
from source.utils import parse_specification_range, Logger
from source.config import AragProduct, ArgsElastic

LOGGER = Logger(name=__file__, log_file="elastic_retriever.log")
LIST_GROUP_PRODUCT = AragProduct.LIST_GROUP_NAME


@dataclass
class ElasticQueryEngine(BaseRetriever):
    cloud_id: str
    api_key: str
    dataframe: pd.DataFrame
    index_name: str="elastic_retriever"
    timeout: int=30
    config = ArgsElastic()

    def __post_init__(self):
        self.client = Elasticsearch(
            cloud_id=self.cloud_id,
            api_key=self.api_key,
            timeout=self.timeout
        )

        if self._count_data() <= 0:
            self.upsert()

    def _count_data(self):
        num_data = self.client.count(index=self.index_name)['count']
        return num_data

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

                LOGGER.log.info("Upsert data to Elastic search client successfull!")
            else:
                pass
        except Exception as e:
            LOGGER.log.error(f"An error occurred while connecting to Elastic Search: {str(e)}")
        
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
            group_product: str, 
            product_name: str, 
            price: Optional[str] = None,
            power: Optional[str] = None,
            weight: Optional[str] = None,
            volume: Optional[str] = None,) -> Dict:
        """
        Tạo một truy vấn Elasticsearch dựa trên các tham số đầu vào.

        Hàm này tạo ra một truy vấn Elasticsearch phức tạp, bao gồm các điều kiện tìm kiếm
        và sắp xếp dựa trên các tham số được cung cấp.

        Args:
            product (str): Tên nhóm sản phẩm chính.
            product_name (str): Tên cụ thể của sản phẩm.
            price (Optional[str]): Giá sản phẩm, có thể bao gồm từ khóa sắp xếp.
            power (Optional[str]): Công suất sản phẩm, có thể bao gồm từ khóa sắp xếp.
            weight (Optional[str]): Trọng lượng sản phẩm, có thể bao gồm từ khóa sắp xếp.
            volume (Optional[str]): Thể tích sản phẩm, có thể bao gồm từ khóa sắp xếp.

        Returns:
            Dict: Một từ điển đại diện cho truy vấn Elasticsearch.

        Note:
            - Hàm này sử dụng hằng số NUMBER_SIZE_ELAS để giới hạn kích thước kết quả trả về.
            - Các tham số tùy chọn (price, power, weight, volume) có thể chứa các từ khóa
            để chỉ định thứ tự sắp xếp (ví dụ: "lớn nhất", "nhỏ nhất").
            - Hàm get_keywords() được sử dụng để phân tích các từ khóa sắp xếp.
            - Hàm create_filter_range() được sử dụng để tạo bộ lọc phạm vi cho các trường số.
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"group_product_name": group_product}},
                        {"match": {"group_name": product_name}}
                    ]
                }
            },
            "size": self.config.top_k
        }

        for field, value in [('lifecare_price', price), 
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
                {"sold_quantity": {"order": "desc"}}
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


    def query(self, demands: Dict[str, Any])-> Tuple[str, List[Dict], int]:

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
                group_product, 
                demands.get("object"), 
                demands.get("price"), 
                demands.get('power'), 
                demands.get('weight'), 
                demands.get('volume')
            )
            queries.append(query)
        
        if len(queries) < 1:
            return None, []
        print("queries: ", queries)

        results = self.bulk_search_products(queries)

        out_text, products_info = "", [] 
        for result in results:
            for i, hit in enumerate(result['hits']['hits']):
                product_details = hit['_source']
                out_text += self.format_output_structure(i, product_details)
                products_info.append({
                    "product_info_id": product_details['product_info_id'],
                    "product_name": product_details['product_name'],
                    "file_path": product_details['file_path']
                })
        return out_text, products_info

    def format_output_structure(self, index: int, product_details: Dict):
        return f"""\n{index + 1}. Tên: '{product_details['product_name']}' 
        - Mã sản phẩm: {product_details['product_info_id']} 
        - Giá: {product_details['lifecare_price']:,.0f} đ
        - Số lượng đã bán: {product_details['sold_quantity']}
        - Thông số : {product_details['specifications']}\n"""