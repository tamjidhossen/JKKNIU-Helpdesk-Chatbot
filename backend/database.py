from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int = Field(foreign_key="user.id")
    
    messages: List["Message"] = Relationship(back_populates="conversation")
    user: "User" = Relationship(back_populates="conversations")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata fields
    query_type: Optional[str] = None
    elapsed_time: Optional[float] = None
    docs_retrieved: Optional[int] = None
    
    conversation: Conversation = Relationship(back_populates="messages")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    conversations: List[Conversation] = Relationship(back_populates="user")

import os
sqlite_url = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), 'helpdesk.db'))}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
