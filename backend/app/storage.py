from tinydb import TinyDB, Query
from typing import Optional, List, Dict, Any
import os
from pathlib import Path
from threading import Lock
import atexit

# Data directory path - use environment variable or default to relative path
DATA_DIR_ENV = os.getenv("DATA_DIR")
if DATA_DIR_ENV:
    DATA_DIR = Path(DATA_DIR_ENV)
else:
    DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database connection cache for reusing connections across operations.
# Thread-safe cache that stores TinyDB instances to avoid repeated open/close cycles.
# Connections are automatically closed on application shutdown via atexit handler.
_db_cache: Dict[str, TinyDB] = {}
_db_lock = Lock()


def _cleanup_connections():
    """Close all cached database connections on shutdown."""
    with _db_lock:
        for db in _db_cache.values():
            db.close()
        _db_cache.clear()


# Register cleanup function to run on application shutdown
atexit.register(_cleanup_connections)


def get_db(table_name: str) -> TinyDB:
    """Get cached TinyDB instance for a specific table/file to reuse connections."""
    with _db_lock:
        if table_name not in _db_cache:
            db_path = DATA_DIR / f"{table_name}.json"
            _db_cache[table_name] = TinyDB(db_path)
        return _db_cache[table_name]


def insert_one(table_name: str, data: Dict[str, Any]) -> str:
    """Insert a single document."""
    db = get_db(table_name)
    doc_id = db.insert(data)
    # Don't close - connection is cached
    return str(doc_id)


def find_all(table_name: str) -> List[Dict[str, Any]]:
    """Get all documents from a table."""
    db = get_db(table_name)
    results = db.all()
    # Don't close - connection is cached
    return results


def find_by_id(table_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Find a document by custom id field."""
    db = get_db(table_name)
    Item = Query()
    result = db.search(Item.id == doc_id)
    # Don't close - connection is cached
    return result[0] if result else None


def find_by_query(table_name: str, query_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find documents matching query."""
    db = get_db(table_name)
    Item = Query()
    
    # Build query dynamically
    query = None
    for key, value in query_dict.items():
        condition = getattr(Item, key) == value
        query = condition if query is None else query & condition
    
    results = db.search(query) if query else db.all()
    # Don't close - connection is cached
    return results


def update_by_id(table_name: str, doc_id: str, updates: Dict[str, Any]) -> bool:
    """Update a document by custom id field."""
    db = get_db(table_name)
    Item = Query()
    result = db.update(updates, Item.id == doc_id)
    # Don't close - connection is cached
    return len(result) > 0


def delete_by_id(table_name: str, doc_id: str) -> bool:
    """Delete a document by custom id field."""
    db = get_db(table_name)
    Item = Query()
    result = db.remove(Item.id == doc_id)
    # Don't close - connection is cached
    return len(result) > 0


def clear_table(table_name: str):
    """Clear all documents from a table."""
    db = get_db(table_name)
    db.truncate()
    # Don't close - connection is cached


def get_single(table_name: str) -> Optional[Dict[str, Any]]:
    """Get single document (for settings/rates tables)."""
    db = get_db(table_name)
    results = db.all()
    # Don't close - connection is cached
    return results[0] if results else None


def upsert_single(table_name: str, data: Dict[str, Any]):
    """Update or insert single document (for settings/rates tables)."""
    db = get_db(table_name)
    db.truncate()
    db.insert(data)
    # Don't close - connection is cached


def batch_update_by_ids(table_name: str, doc_ids: List[str], updates: Dict[str, Any]) -> int:
    """Batch update multiple documents by their custom id fields.
    Returns the count of documents updated."""
    db = get_db(table_name)
    Item = Query()
    
    # Use a single query to update all matching documents
    result = db.update(updates, Item.id.test(lambda x: x in doc_ids))
    # Don't close - connection is cached
    return len(result)


def batch_delete_by_ids(table_name: str, doc_ids: List[str]) -> int:
    """Batch delete multiple documents by their custom id fields.
    Returns the count of documents deleted."""
    db = get_db(table_name)
    Item = Query()
    
    # Use a single query to delete all matching documents
    result = db.remove(Item.id.test(lambda x: x in doc_ids))
    # Don't close - connection is cached
    return len(result)
