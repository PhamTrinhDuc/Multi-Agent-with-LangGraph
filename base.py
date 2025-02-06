
from dataclasses import dataclass, field
from typing import Union, Generic, TypeVar, List, Dict, Tuple, Literal, Optional
from abc import ABC, abstractmethod

@dataclass
class BaseVectorStorage(ABC):

    @abstractmethod
    async def query(self, query: str) -> List[dict]:
        raise NotImplementedError
    
    @abstractmethod
    async def upsert(self):
        """
        Use 'content' field from value for embedding, use key as id.
        If embedding_func is None, use 'embedding' field from value
        """
        raise NotImplementedError
    
    async def index_done_callback(self):
        "commit the storage operations after indexing"
        pass

    async def query_done_callback(self):
        "commit the storage operations after querying"
        pass


@dataclass
class BaseProcessData:

    def get_metadata(self):
        """get metadata from excel file"""
        raise NotImplementedError
    
    def create_document(self):
        """format data excel file to Document"""
        raise NotImplemented