"""Constants necessaries for build the Sortex"""
from pathlib import Path
from settings import load_settings

def yield_absolute_path_from(relative_path: str):
    path_instance = Path(relative_path)
    return path_instance.expanduser() if relative_path.startswith('~') else path_instance

default_settings = load_settings()
user_settings = {}

# Avoid import them. These key are used mainly for easy reading and maintenance
KEY_THREADS_SECTION = "threads-section"
KEY_DIRECTORIES_SECTION = "directories-section"
KEY_SET_DIRECTORY = "sort_directory"
KEY_EXCLUDE_DIRECTORIES = "exclude_directories"
KEY_MAX_WORKERS = "max_workers"

DEFAULT_SLOT_THREADS_SECTION = default_settings[KEY_THREADS_SECTION]
DEFAULT_SLOT_DIRECTORIES_SECTION = default_settings[KEY_DIRECTORIES_SECTION]

# Here constants with slot prefix implie sub-sections, pratically dictionaries.
SLOT_THREADS_SECTION = user_settings.get(KEY_THREADS_SECTION, DEFAULT_SLOT_THREADS_SECTION)
SLOT_DIRECTORIES_SECTION = user_settings.get(KEY_DIRECTORIES_SECTION, DEFAULT_SLOT_DIRECTORIES_SECTION)

# Constants that are allowed to import
MAX_WORKERS: int = SLOT_THREADS_SECTION.get(KEY_MAX_WORKERS, DEFAULT_SLOT_THREADS_SECTION[KEY_MAX_WORKERS])
SET_DIRECTORY: str = SLOT_DIRECTORIES_SECTION.get(KEY_SET_DIRECTORY, DEFAULT_SLOT_DIRECTORIES_SECTION[KEY_SET_DIRECTORY])
SET_DIRECTORY: Path = yield_absolute_path_from(SET_DIRECTORY)
EXCLUDED_DIRECTORIES: list = SLOT_DIRECTORIES_SECTION.get(KEY_EXCLUDE_DIRECTORIES, DEFAULT_SLOT_DIRECTORIES_SECTION[KEY_EXCLUDE_DIRECTORIES])