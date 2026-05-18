"""
Modèles SQLAlchemy pour PostgreSQL
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, 
    DateTime, JSON, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()


class Conversation(Base):
    """Table des conversations"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_identifier = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default=dict)
    
    # Relations
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_conversation_session', 'session_id'),
        Index('idx_conversation_created', 'created_at'),
    )


class Message(Base):
    """Table des messages"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    response_id = Column(String(100), nullable=True)  # Pour les réponses assistant
    llm_provider = Column(String(50), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    articles_referenced = Column(ARRAY(Integer), default=list)
    cached = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False)
    
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_created', 'created_at'),
        Index('idx_message_response_id', 'response_id'),
    )


class Feedback(Base):
    """Table des feedbacks"""
    __tablename__ = "feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    helpful = Column(Boolean, default=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    message = relationship("Message", back_populates="feedback")
    
    __table_args__ = (
        Index('idx_feedback_message', 'message_id'),
        Index('idx_feedback_rating', 'rating'),
    )


class QuestionLog(Base):
    """Log des questions pour analytics"""
    __tablename__ = "question_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    question_hash = Column(String(64), nullable=False, index=True)  # SHA256
    category = Column(String(50), nullable=True)
    llm_provider = Column(String(50), nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=True)
    was_cached = Column(Boolean, default=False)
    articles_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_qlog_hash', 'question_hash'),
        Index('idx_qlog_created', 'created_at'),
        Index('idx_qlog_category', 'category'),
    )


class Article(Base):
    """Cache des articles de la loi dans PostgreSQL"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    numero = Column(Integer, unique=True, nullable=False, index=True)
    contenu = Column(Text, nullable=False)
    theme_principal = Column(String(100), nullable=True)
    themes_secondaires = Column(ARRAY(String), default=list)
    mots_cles = Column(ARRAY(String), default=list)
    entites_concernees = Column(ARRAY(String), default=list)
    type_disposition = Column(String(50), nullable=True)
    valeurs_numeriques = Column(JSON, default=dict)
    embedding_id = Column(String(100), nullable=True)  # ID dans Qdrant
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_article_numero', 'numero'),
        Index('idx_article_theme', 'theme_principal'),
    )


class CacheEntry(Base):
    """Cache des réponses fréquentes"""
    __tablename__ = "cache_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_hash = Column(String(64), unique=True, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    articles_references = Column(JSON, default=list)
    suggested_questions = Column(JSON, default=list)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index('idx_cache_hash', 'question_hash'),
        Index('idx_cache_expires', 'expires_at'),
    )


class SystemStats(Base):
    """Statistiques du système"""
    __tablename__ = "system_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True)
    total_questions = Column(Integer, default=0)
    unique_sessions = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    llm_calls = Column(JSON, default=dict)  # Par provider
    categories_distribution = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_stats_date', 'date'),
    )
