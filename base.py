
from dataclasses import dataclass, field
from typing import Union, Generic, TypeVar, List, Dict, Tuple, Literal, Optional
from abc import ABC, abstractmethod

@dataclass
class BaseRetriever(ABC):

    @abstractmethod
    def create_client(self):
        raise NotImplementedError

    @abstractmethod
    async def query(self, query: str, *args, **kwargs) -> List[dict]:
        raise NotImplementedError
    
    @abstractmethod
    async def upsert(self):
        """
        Use 'content' field from value for embedding, use key as id.
        If embedding_func is None, use 'embedding' field from value
        """
        raise NotImplementedError
    
    @abstractmethod
    def format_output_structure(self):
        raise NotImplementedError
    

@dataclass
class BaseDocumentStorage:

    def create_metadata(self):
        """create metadata from excel file"""
        raise NotImplementedError
    
    def create_document(self):
        """format data excel file to Document"""
        raise NotImplemented
