from pathlib import Path

from .utils.appdirs import user_cache_dir
from .utils.appdirs import user_config_dir
from .utils.appdirs import user_data_dir


CACHE_DIR = user_cache_dir("pypoetry")
DATA_DIR = user_data_dir("pypoetry")
CONFIG_DIR = user_config_dir("pypoetry")

REPOSITORY_CACHE_DIR = Path(CACHE_DIR) / "cache" / "repositories"
