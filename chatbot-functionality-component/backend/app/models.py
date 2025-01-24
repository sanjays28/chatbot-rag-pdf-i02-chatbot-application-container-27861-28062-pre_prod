from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# PUBLIC_INTERFACE
class User(Base):
    """User model for storing user information."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")

# PUBLIC_INTERFACE
class PDFDocument(Base):
    """Model for storing PDF document information."""
    __tablename__ = 'pdf_documents'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default='pending')  # pending, processing, completed, error
    metadata = Column(JSON)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document")

# PUBLIC_INTERFACE
class ChatSession(Base):
    """Model for storing chat session information."""
    __tablename__ = 'chat_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

# PUBLIC_INTERFACE
class ChatMessage(Base):
    """Model for storing chat messages."""
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.id'), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String(20), nullable=False)  # user, assistant

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

# PUBLIC_INTERFACE
class DocumentChunk(Base):
    """Model for storing document chunks with their embeddings."""
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('pdf_documents.id'), nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(JSON)  # Store vector embeddings as JSON

    # Relationships
    document = relationship("PDFDocument", back_populates="chunks")