# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from base import BaseKVStorage
import os
from dataclasses import dataclass
from typing import List, Dict, Any
from source.base import BaseKVStorage
from source.utils import write_json, load_json, Logger


LOGGER = Logger(name=__file__, log_file="json_cache.log")


@dataclass
class JsonKVStorage(BaseKVStorage):
    kv_file_name: str
    working_dir: str = "working_dir"

    def __post_init__(self):
        self.file_path = os.path.join(self.working_dir, f"{self.kv_file_name}.json")
        self.data_json = load_json(file_name=self.file_path)
        LOGGER.log.info(f"Load kv cache with {len(self.data_json)} data")
    
    def all_keys(self) -> List[str]:
        """Get all keys in current data"""
        return self._data_json.keys()

    def get_by_id(self, id: str) -> dict:
        """Get json data by id from current data"""
        return self._data_json.get(id, None)

    def filter_keys(self, data: list[str]) -> set[str]:
        """Get keys in data that not in current data"""
        return set([key for key in data if key not in self._data_json])

    def upsert(self, data: Dict[str, Dict[str, Any]]) -> None:
        left_data = {k: v for k, v in data.items() if k not in self._data_json}
        self._data_json.update(left_data)
    
    def drop(self):
        self._data_json = {}

    def index_done_callback(self):
        """Write data to json file after indexing"""
        write_json(json_obj=self._data_json, file_name=self._file_name_data)
    

