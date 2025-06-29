import os
import sys
from pathlib import Path  # Better path handling
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from loguru import logger

# Fix for relative imports - ensure this matches your project structure
try:
    from src.database.models import Base
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent.parent))  # Add project root to PATH
    from src.database.models import Base

def setup_directories():
    """Create necessary directories for the project with better path handling."""
    directories = [
        'logs',
        'data',
        os.path.join('src', 'templates', 'emails'),  # Cross-platform path
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory verified: {directory}")

def setup_logging():
    """Configure logging settings with enhanced error handling."""
    try:
        log_file = Path(os.getenv('LOG_FILE', 'logs/app.log'))
        log_file.parent.mkdir(exist_ok=True)  # Ensure log directory exists
        
        logger.add(
            str(log_file),
            rotation="500 MB",
            retention="10 days",
            level=os.getenv('LOG_LEVEL', 'INFO'),
            enqueue=True  # Thread-safe logging
        )
    except Exception as e:
        logger.error(f"Logging setup failed: {str(e)}")
        raise

def init_database():
    """Initialize the database with improved error recovery."""
    try:
        load_dotenv()
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        engine = create_engine(database_url, pool_pre_ping=True)  # Add connection health checks
        
        # Verify connection before creating tables
        with engine.connect() as test_conn:
            test_conn.execute("SELECT 1")
        
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        
        logger.success(f"Database initialized at {database_url}")
        return Session()
        
    except Exception as e:
        logger.critical(f"Database initialization failed: {str(e)}")
        sys.exit(1)

def main():
    """Main initialization function with better cleanup."""
    session = None
    try:
        setup_directories()
        setup_logging()
        logger.info("Initializing application...")
        
        session = init_database()
        logger.success("Application initialized successfully")
        return session
        
    except Exception as e:
        logger.critical(f"Fatal initialization error: {str(e)}")
        if session:
            session.close()
        sys.exit(1)

if __name__ == '__main__':
    main()