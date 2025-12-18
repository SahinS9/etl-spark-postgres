"""
Initialize the database schema
"""

from .db import get_engine
from .models import Base

def main() -> None:
    engine = get_engine()

    print("[init_db.py] creating/verifying tables...")
    Base.metadata.create_all(engine)
    print("init_db.py] Tables created/verified!")

if __name__ == "__main__":
    main()
