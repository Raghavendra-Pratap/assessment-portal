"""Database initialization and models"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    assessments = relationship("Assessment", back_populates="recruiter")

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
    
    recruiter = relationship("Recruiter", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="assessment", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="assessment", cascade="all, delete-orphan")

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
    
    assessment = relationship("Assessment", back_populates="questions")
    responses = relationship("Response", back_populates="question", cascade="all, delete-orphan")

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
    
    assessment = relationship("Assessment", back_populates="invitations")

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
    
    assessment = relationship("Assessment", back_populates="sessions")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")
    monitoring_events = relationship("MonitoringEvent", back_populates="session", cascade="all, delete-orphan")

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
    
    session = relationship("Session", back_populates="responses")
    question = relationship("Question", back_populates="responses")

class MonitoringEvent(Base):
    __tablename__ = 'monitoring_events'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # tab_change, copy_paste, fullscreen_exit, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)
    severity = Column(String(20), default='low')  # low, medium, high
    metadata = Column(Text)
    
    session = relationship("Session", back_populates="monitoring_events")

