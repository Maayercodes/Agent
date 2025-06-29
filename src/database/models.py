from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy base class
Base = declarative_base()

class Region(enum.Enum):
    USA = "USA"
    FRANCE = "FRANCE"

class Platform(enum.Enum):
    YOUTUBE = "YOUTUBE"
    INSTAGRAM = "INSTAGRAM"

class Daycare(Base):
    __tablename__ = 'daycares'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    city = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(500))
    region = Column(Enum(Region), nullable=False)
    source = Column(String(100))  # e.g., 'yelp', 'care.com', etc.
    last_contacted = Column(DateTime)
    email_opened = Column(Boolean, default=False)
    email_replied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Daycare(name='{self.name}', city='{self.city}', region='{self.region.value}')>"

class Influencer(Base):
    __tablename__ = 'influencers'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    follower_count = Column(Integer)
    country = Column(String(100))
    email = Column(String(255))
    bio = Column(Text)
    contact_page = Column(String(500))
    niche = Column(String(100))  # e.g., 'parenting', 'education', 'kids'
    last_contacted = Column(DateTime)
    email_opened = Column(Boolean, default=False)
    email_replied = Column(Boolean, default=False)
    engagement_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Influencer(name='{self.name}', platform='{self.platform.value}', followers='{self.follower_count}')>"

class OutreachHistory(Base):
    __tablename__ = 'outreach_history'

    id = Column(Integer, primary_key=True)
    target_type = Column(String(50))  # 'daycare' or 'influencer'
    target_id = Column(Integer, nullable=False)
    email_subject = Column(String(255))
    email_content = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    replied_at = Column(DateTime)
    bounced = Column(Boolean, default=False)
    language = Column(String(10))  # 'en' or 'fr'

    def __repr__(self):
        return f"<OutreachHistory(target_type='{self.target_type}', target_id='{self.target_id}', sent_at='{self.sent_at}')>"

# Database connection setup
def init_db():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    
    # Create session factory
    Session = sessionmaker(bind=engine)
    return Session()

# Create tables if they don't exist
if __name__ == '__main__':
    init_db()
    print("Database tables created successfully!")
