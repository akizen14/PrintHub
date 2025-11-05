from tinydb import TinyDB, Query
from typing import Optional, List, Dict, Any
import os
from pathlib import Path

# Data directory path - relative to backend folder
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def get_db(table_name: str) -> TinyDB:
    """Get TinyDB instance for a specific table/file."""
    db_path = DATA_DIR / f"{table_name}.json"
    return TinyDB(db_path)


def insert_one(table_name: str, data: Dict[str, Any]) -> str:
    """Insert a single document."""
    db = get_db(table_name)
    doc_id = db.insert(data)
    db.close()
    return str(doc_id)


def find_all(table_name: str) -> List[Dict[str, Any]]:
    """Get all documents from a table."""
    db = get_db(table_name)
    results = db.all()
    db.close()
    return results


def find_by_id(table_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Find a document by custom id field."""
    db = get_db(table_name)
    Item = Query()
    result = db.search(Item.id == doc_id)
    db.close()
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
    db.close()
    return results


def update_by_id(table_name: str, doc_id: str, updates: Dict[str, Any]) -> bool:
    """Update a document by custom id field."""
    db = get_db(table_name)
    Item = Query()
    result = db.update(updates, Item.id == doc_id)
    db.close()
    return len(result) > 0


def delete_by_id(table_name: str, doc_id: str) -> bool:
    """Delete a document by custom id field."""
    db = get_db(table_name)
    Item = Query()
    result = db.remove(Item.id == doc_id)
    db.close()
    return len(result) > 0


def clear_table(table_name: str):
    """Clear all documents from a table."""
    db = get_db(table_name)
    db.truncate()
    db.close()


def get_single(table_name: str) -> Optional[Dict[str, Any]]:
    """Get single document (for settings/rates tables)."""
    db = get_db(table_name)
    results = db.all()
    db.close()
    return results[0] if results else None


def upsert_single(table_name: str, data: Dict[str, Any]):
    """Update or insert single document (for settings/rates tables)."""
    db = get_db(table_name)
    db.truncate()
    db.insert(data)
    db.close()
