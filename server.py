from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import Session, select
from database import engine, create_db_and_tables, get_session, Conversation, Message
from main_enhanced import EnhancedChatbot
import uvicorn
from contextlib import asynccontextmanager

# Initialize chatbot
chatbot = EnhancedChatbot(use_enhanced=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    create_db_and_tables()
    yield

app = FastAPI(title="JKKNIU Helpdesk API", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

class MessageSchema(BaseModel):
    id: int
    role: str
    content: str
    query_type: Optional[str] = None
    elapsed_time: Optional[float] = None
    docs_retrieved: Optional[int] = None

class ConversationSchema(BaseModel):
    id: int
    title: str
    created_at: str

@app.post("/chat")
async def chat(request: ChatRequest, session: Session = Depends(get_session)):
    # 1. Get or create conversation
    if request.conversation_id:
        db_conversation = session.get(Conversation, request.conversation_id)
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation with title from the first message
        title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        db_conversation = Conversation(title=title)
        session.add(db_conversation)
        session.commit()
        session.refresh(db_conversation)
    
    # 2. Save user message
    user_msg = Message(
        conversation_id=db_conversation.id,
        role="user",
        content=request.message
    )
    session.add(user_msg)
    session.commit() # Commit here so history fetch is accurate
    session.refresh(user_msg)
    
    # Fetch history for context (last 10 messages)
    history_msgs = session.exec(
        select(Message)
        .where(Message.conversation_id == db_conversation.id)
        .order_by(Message.created_at.desc())
        .limit(11) # user message + 10 previous
    ).all()
    
    # Format history (excluding current user message which is history_msgs[0])
    history_text = ""
    # history_msgs[0] is current user message
    for msg in reversed(history_msgs[1:]): 
        role_label = "Student" if msg.role == "user" else "Assistant"
        history_text += f"{role_label}: {msg.content}\n"
    
    # 3. Get AI response
    result = chatbot.ask(request.message, history=history_text)
    
    if result["error"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # 4. Save assistant message
    ai_msg = Message(
        conversation_id=db_conversation.id,
        role="assistant",
        content=result["response"],
        query_type=result["query_type"],
        elapsed_time=result["elapsed_time"],
        docs_retrieved=result["docs_retrieved"]
    )
    session.add(ai_msg)
    session.commit()
    session.refresh(ai_msg)
    
    return {
        "conversation_id": db_conversation.id,
        "response": result["response"],
        "metadata": {
            "query_type": result["query_type"],
            "elapsed_time": result["elapsed_time"],
            "docs_retrieved": result["docs_retrieved"]
        }
    }

@app.get("/conversations", response_model=List[ConversationSchema])
async def get_conversations(session: Session = Depends(get_session)):
    statement = select(Conversation).order_by(Conversation.created_at.desc())
    results = session.exec(statement).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in results]

@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageSchema])
async def get_messages(conversation_id: int, session: Session = Depends(get_session)):
    statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    results = session.exec(statement).all()
    return results

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, session: Session = Depends(get_session)):
    db_conversation = session.get(Conversation, conversation_id)
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Messages will be deleted if cascaded, but SQLModel Relationship doesn't do cascade by default in DB level easily without extra config
    # For simplicity, delete messages manually
    statement = select(Message).where(Message.conversation_id == conversation_id)
    messages = session.exec(statement).all()
    for msg in messages:
        session.delete(msg)
        
    session.delete(db_conversation)
    session.commit()
    return {"message": "Conversation deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
