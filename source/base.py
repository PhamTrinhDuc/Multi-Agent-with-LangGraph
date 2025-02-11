
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any

@dataclass
class BaseRetriever(ABC):

    @abstractmethod
    async def query(self, query: str, *args, **kwargs) -> str:
        """Perform retrieval document from user's query"""
        raise NotImplementedError
    
    @abstractmethod
    async def upsert(self, *args, **kwargs):
        """
        Use 'content' field from value for embedding, use key as id.
        If embedding_func is None, use 'embedding' field from value
        """
        raise NotImplementedError
    
    def format_output_structure(self, *args, **kwargs) -> str:
        """Reponse retriever's output"""
        raise NotImplementedError
    

@dataclass 
class BaseKVStorage(ABC):

    @abstractmethod
    async def all_keys(self) -> List[str]:
        """Get all keys in current data"""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Union[Any, None]:
        """Get data by id from current data"""
        raise NotImplementedError
    
    @abstractmethod
    async def filter_keys(self, data: List[str]) -> set[str]:
        """Get keys in data that not in current data"""
        raise NotImplementedError
    
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]):
        raise NotImplementedError