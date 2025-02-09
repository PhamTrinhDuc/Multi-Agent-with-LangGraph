import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

sys.path.append(str(Path(__file__).parent))


class LoggingConfig:
    ROOT_DIR = Path(__file__).parent # cd to root folder

    # SOURCE_DIR = ROOT_DIR / "src" # cd to src folder
    LOG_DIR = ROOT_DIR / "logs"

LoggingConfig.LOG_DIR.mkdir(parents=True, exist_ok=True) # create logs folder in src 


class Logger:
    def __init__(self,
                 name="", 
                 log_level: str=logging.INFO,
                 log_file=None):
        self.log = logging.getLogger(name=name)
        self.get_logger(log_level, log_file)

    def get_logger(self, log_level: str, log_file: str):
        self.log.setLevel(level=log_level)
        self._init_formatter()

        if log_file is not None: # if log_file exist
            self._add_file_handler(log_file=LoggingConfig.LOG_DIR/log_file)
        else: # print log to console
            self._add_stream_handler()
    
    def _init_formatter(self):
        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def _add_stream_handler(self):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(self.formatter)
        self.log.addHandler(stream_handler)
    
    def _add_file_handler(self, log_file: Path):
        file_handler = RotatingFileHandler(filename=log_file, maxBytes=10000, backupCount=10)
        file_handler.setFormatter(self.formatter)
        self.log.addHandler(file_handler)