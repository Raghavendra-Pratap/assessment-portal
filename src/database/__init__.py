"""Database initialization and models"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'assessments.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create engine
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# Session factory
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Add missing columns to existing tables (migration)
    try:
        with engine.connect() as conn:
            # Check if is_admin column exists in recruiters table
            result = conn.execute("PRAGMA table_info(recruiters)")
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_admin' not in columns:
                # Add is_admin column
                conn.execute("ALTER TABLE recruiters ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                conn.commit()
                print("Added is_admin column to recruiters table")
    except Exception as e:
        print(f"Migration warning: {e}")
        # Continue anyway - the column might already exist

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class Recruiter(Base):
    __tablename__ = 'recruiters'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    company = Column(String(255), default='')
    dashboard_slug = Column(String(100), unique=True, nullable=False)
    branding_settings = Column(JSON, default={})
    storage_config = Column(JSON, default={})
    status = Column(String(20), default='active')
    is_admin = Column(Boolean, default=False)  # Admin flag - only admins can access admin panel
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    assessments = relationship("Assessment", back_populates="recruiter", lazy="select")

class Assessment(Base):
    __tablename__ = 'assessments'
    
    id = Column(Integer, primary_key=True)
    recruiter_id = Column(Integer, ForeignKey('recruiters.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=60)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    recruiter = relationship("Recruiter", back_populates="assessments", lazy="select")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan", lazy="select")
    sessions = relationship("Session", back_populates="assessment", cascade="all, delete-orphan", lazy="select")
    invitations = relationship("Invitation", back_populates="assessment", cascade="all, delete-orphan", lazy="select")

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'), nullable=False)
    type = Column(String(50), default='formula')  # formula, data-entry, mcq, scenario
    question_text = Column(Text, nullable=False)
    sheet_template_url = Column(Text)
    answer_key = Column(JSON)
    points = Column(Integer, default=10)
    display_order = Column(Integer, default=0)
    section_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assessment = relationship("Assessment", back_populates="questions", lazy="select")
    responses = relationship("Response", back_populates="question", cascade="all, delete-orphan", lazy="select")

class Invitation(Base):
    __tablename__ = 'invitations'
    
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'), nullable=False)
    recruiter_id = Column(Integer, ForeignKey('recruiters.id'), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    candidate_name = Column(String(255), default='')
    unique_token = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default='sent')  # sent, started, completed, expired
    sent_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    google_email = Column(String(255), default='')
    
    assessment = relationship("Assessment", back_populates="invitations", lazy="select")

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    unique_token = Column(String(64), unique=True, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    ip_address = Column(String(45))
    status = Column(String(50), default='pending')  # pending, in_progress, completed, expired
    suspicion_score = Column(Integer, default=0)
    final_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assessment = relationship("Assessment", back_populates="sessions", lazy="select")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan", lazy="select")
    # monitoring_events relationship moved after MonitoringEvent class definition

class Response(Base):
    __tablename__ = 'responses'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    sheet_url = Column(Text)
    auto_score = Column(Float)
    manual_score = Column(Float)
    reviewer_notes = Column(Text)
    graded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="responses", lazy="select")
    question = relationship("Question", back_populates="responses", lazy="select")

class MonitoringEvent(Base):
    __tablename__ = 'monitoring_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # tab_change, copy_paste, fullscreen_exit, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)
    severity = Column(String(20), default='low')  # low, medium, high
    event_metadata = Column('metadata', Text)  # Column name in DB is 'metadata', but attribute is 'event_metadata' to avoid conflict

# Configure the relationship on Session after MonitoringEvent is fully defined
# This breaks the circular dependency that causes InvalidRequestError in SQLAlchemy 2.0+
from sqlalchemy.orm import configure_mappers

# Add the relationship attribute to Session after MonitoringEvent is defined
Session.monitoring_events = relationship(
    "MonitoringEvent",
    foreign_keys=[MonitoringEvent.session_id],
    back_populates="session",
    cascade="all, delete-orphan",
    lazy="select"
)

# Add the relationship attribute to MonitoringEvent  
MonitoringEvent.session = relationship(
    "Session",
    foreign_keys=[MonitoringEvent.session_id],
    back_populates="monitoring_events",
    lazy="select"
)

# Configure all mappers now that all relationships are defined
configure_mappers()

