import pandas as pd
from dataclasses import dataclass, field

@dataclass
class AragProduct:
    DATA_PATH: str = "product_variant.csv"
    LIST_GROUP_NAME = pd.unique(pd.read_csv(DATA_PATH)['category_name'].tolist())
    CACHE_PATH: str = "data/cache/sqlite.db"
    
@dataclass
class ArgQdrant:
    top_k: int=3
    dimension_vector: int=768
    score_threshold: float = 0.5
    is_with_payload: bool = True
    is_with_vector: bool = False

@dataclass 
class ArgChroma:
    top_k: int=3
    collection_name: str="chroma_db"
    db_persist_path: str="data/db/chroma_db"
    weights_ensemble: list = field(default_factory=lambda: [0.5, 0.5])
    lambda_mult: float=0.25
    fetch_k: int=20
    score_threshold: float=0.75

@dataclass
class ArgsElastic:
    top_k: int=3