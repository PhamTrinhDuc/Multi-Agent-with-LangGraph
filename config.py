import pandas as pd
from dataclasses import dataclass

@dataclass
class AragProduct:
    # PRODUCTION
    DATA_PATH: str = "data/300productions.xlsx"
    LIST_GROUP_NAME = pd.unique(pd.read_excel(DATA_PATH)['group_product_name'].tolist())
    
    # ELASTIC SEARCH
    NUM_SIZE_ELASTIC = 3
