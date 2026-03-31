from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from pydantic import BaseModel
import json
import os
import uuid
import glob
from typing import List, Dict, Optional
from datetime import datetime
import uvicorn
from source.graph import GraphEcommerce
from langchain.messages import HumanMessage

app = FastAPI(title="E-commerce Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graph
graph_instance = None

def get_graph():
    global graph_instance
    if graph_instance is None:
        graph_instance = GraphEcommerce().init_graph()
    return graph_instance

# Pydantic models
class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    question: str

class ChatResponse(BaseModel):
    user_id: str
    session_id: str
    question: str
    answer: str
    products: Optional[List[Dict]] = []
    is_order: Optional[bool] = False
    timestamp: str

class SessionInfo(BaseModel):
    session_id: str
    title: str
    updated_at: str

class UserSessionsResponse(BaseModel):
    user_id: str
    sessions: List[SessionInfo]

class ConversationHistory(BaseModel):
    user_id: str
    session_id: str
    messages: List[Dict]

# Helper functions
def ensure_history_dir():
    os.makedirs("./history", exist_ok=True)

def load_history(session_id: str) -> List[Dict]:
    ensure_history_dir()
    try:
        with open(f"./history/session_{session_id}.json", 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    except FileNotFoundError:
        return []

def save_history(session_id: str, history: List[Dict]):
    ensure_history_dir()
    with open(f"./history/session_{session_id}.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_user_sessions(user_id: str) -> List[Dict]:
    ensure_history_dir()
    try:
        with open(f"./history/user_{user_id}_sessions.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_user_sessions(user_id: str, sessions: List[Dict]):
    ensure_history_dir()
    with open(f"./history/user_{user_id}_sessions.json", 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "E-commerce Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "POST - Send a message",
            "/sessions/{user_id}": "GET - Get list of sessions for user",
            "/conversation/{session_id}": "GET - Get conversation history",
            "/conversation/{user_id}/{session_id}": "DELETE - Clear conversation history",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response from the chatbot"""
    try:
        # Generate new session ID if missing
        session_id = request.session_id if request.session_id else str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Load user sessions to see if this is a new one
        user_sessions = load_user_sessions(request.user_id)
        session_exists = any(s['session_id'] == session_id for s in user_sessions)
        
        if not session_exists:
            title_text = request.question[:30] + "..." if len(request.question) > 30 else request.question
            user_sessions.append({
                "session_id": session_id,
                "title": title_text,
                "updated_at": timestamp
            })
        else:
            for s in user_sessions:
                if s['session_id'] == session_id:
                    s['updated_at'] = timestamp
        
        save_user_sessions(request.user_id, user_sessions)

        graph = get_graph()
        config = {"configurable": {"thread_id": session_id}}
        
        # Invoke the graph
        result = graph.invoke(
            {"question": HumanMessage(content=request.question)},
            config=config
        )
        
        # Extract the answer from the result
        answer = ""
        products = []
        is_order = False
        
        if 'messages' in result and len(result['messages']) > 0:
            last_message = result['messages'][-1]
            answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
        if 'products' in result:
            products = result['products']
            
        if 'is_order' in result:
            is_order = result['is_order']
        
        # Save to history
        history = load_history(session_id)
        history.append({
            "role": "user",
            "content": request.question,
            "timestamp": timestamp
        })
        history.append({
            "role": "assistant",
            "content": answer,
            "products": products,
            "is_order": is_order,
            "timestamp": timestamp
        })
        save_history(session_id, history)
        
        return ChatResponse(
            user_id=request.user_id,
            session_id=session_id,
            question=request.question,
            answer=answer,
            products=products,
            is_order=is_order,
            timestamp=timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/sessions/{user_id}", response_model=UserSessionsResponse)
async def get_user_sessions(user_id: str):
    """Get all conversation sessions for a user"""
    try:
        sessions = load_user_sessions(user_id)
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return UserSessionsResponse(user_id=user_id, sessions=sessions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

@app.get("/conversation/{session_id}", response_model=ConversationHistory)
async def get_conversation(session_id: str):
    """Get conversation history for a specific session"""
    try:
        history = load_history(session_id)
        return ConversationHistory(user_id="unknown", session_id=session_id, messages=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@app.delete("/conversation/{user_id}/{session_id}")
async def clear_conversation(user_id: str, session_id: str):
    """Delete a specific conversation session"""
    try:
        # Delete history file
        history_file = f"./history/session_{session_id}.json"
        if os.path.exists(history_file):
            os.remove(history_file)
            
        # Update user sessions list
        user_sessions = load_user_sessions(user_id)
        user_sessions = [s for s in user_sessions if s['session_id'] != session_id]
        save_user_sessions(user_id, user_sessions)
        
        return {"message": f"Session {session_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

@app.get("/message")
async def get_message(
    user_id: str = Query(..., description="User ID của người dùng"),
    session_id: Optional[str] = Query(None, description="Session ID của người dùng"),
    question: str = Query(..., description="Câu hỏi của người dùng"),
):
    """Legacy endpoint - use /chat instead"""
    try:
        request = ChatRequest(user_id=user_id, session_id=session_id, question=question)
        response = await chat(request)
        return JSONResponse(
            status_code=200,
            content={
                "answer": response.answer,
                "timestamp": response.timestamp
            }
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)