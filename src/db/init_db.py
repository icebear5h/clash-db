import os
import sys
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Base
from db.config import engine

def init_db():
    """Initialize the database and create all tables."""
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment or use default
    db_url = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:password@localhost/clash_royale')
    
    # Create engine
    engine = create_engine(db_url)
    
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        print(f"Creating database: {engine.url.database}")
        create_database(engine.url)
    
    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
