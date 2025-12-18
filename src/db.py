"""
Database utilities
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .config import DATABASE_URL, validate_config

_engine: Engine | None = None #lazy initialization #not connecting on import but on function execution

def get_engine() -> Engine:
    global _engine

    if _engine is not None:
        return _engine
    
    #Ensures DATABASE_URL exists (and config is loaded)
    validate_config()
    
    _engine = create_engine(DATABASE_URL, pool_pre_ping=True) #avoids common stale connection issues
    return _engine