from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import Session, select
from database import engine, create_db_and_tables, get_session, Conversation, Message
from main_enhanced import EnhancedChatbot
import uvicorn
from contextlib import asynccontextmanager
from database import User
from auth_utils import get_password_hash, verify_password, create_access_token, send_verification_email
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
import uuid

# Initialize chatbot
chatbot = EnhancedChatbot(use_enhanced=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return user

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
    response_type: Optional[str] = "elaborative"

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserSchema(BaseModel):
    id: int
    email: str
    is_verified: bool

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

@app.post("/auth/register", response_model=UserSchema)
async def register(user_in: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user_in.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    verification_token = str(uuid.uuid4())
    
    new_user = User(
        email=user_in.email, 
        password_hash=hashed_password,
        verification_token=verification_token,
        is_verified=False
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Send email
    send_verification_email(new_user.email, verification_token)
    
    return new_user

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/verify/{token}")
async def verify_email(token: str, session: Session = Depends(get_session)):
    statement = select(User).where(User.verification_token == token)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    user.is_verified = True
    # user.verification_token = None # Keep token to allow "Already verified" message on re-clicks
    session.add(user)
    session.commit()
    return {"message": "Email verified successfully"}

@app.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/chat")
async def chat(request: ChatRequest, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
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
    result = chatbot.ask(request.message, history=history_text, response_type=request.response_type)
    
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
