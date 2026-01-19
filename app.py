from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from pydantic import BaseModel
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import uvicorn
import sys
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
    question: str

class ChatResponse(BaseModel):
    user_id: str
    question: str
    answer: str
    timestamp: str

class ConversationHistory(BaseModel):
    user_id: str
    messages: List[Dict[str, str]]

# Helper functions
def ensure_history_dir():
    os.makedirs("./history", exist_ok=True)

def load_history(user_id: str) -> List[Dict]:
    ensure_history_dir()
    try:
        with open(f"./history/{user_id}.json", 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                return history
            except json.JSONDecodeError:
                return []
    except FileNotFoundError:
        return []

def save_history(user_id: str, history: List[Dict]):
    ensure_history_dir()
    with open(f"./history/{user_id}.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "E-commerce Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "/chat": "POST - Send a message",
            "/conversation/{user_id}": "GET - Get conversation history",
            "/conversation/{user_id}": "DELETE - Clear conversation history",
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
        graph = get_graph()
        config = {"configurable": {"thread_id": request.user_id}}
        
        # Invoke the graph
        result = graph.invoke(
            {"question": HumanMessage(content=request.question)},
            config=config
        )
        
        # Extract the answer from the result
        answer = ""
        if 'messages' in result and len(result['messages']) > 0:
            last_message = result['messages'][-1]
            answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Save to history
        timestamp = datetime.now().isoformat()
        history = load_history(request.user_id)
        history.append({
            "role": "user",
            "content": request.question,
            "timestamp": timestamp
        })
        history.append({
            "role": "assistant",
            "content": answer,
            "timestamp": timestamp
        })
        save_history(request.user_id, history)
        
        return ChatResponse(
            user_id=request.user_id,
            question=request.question,
            answer=answer,
            timestamp=timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/conversation/{user_id}", response_model=ConversationHistory)
async def get_conversation(user_id: str):
    """Get conversation history for a user"""
    try:
        history = load_history(user_id)
        return ConversationHistory(user_id=user_id, messages=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@app.delete("/conversation/{user_id}")
async def clear_conversation(user_id: str):
    """Clear conversation history for a user"""
    try:
        ensure_history_dir()
        history_file = f"./history/{user_id}.json"
        if os.path.exists(history_file):
            os.remove(history_file)
        return {"message": f"Conversation history cleared for user {user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

@app.get("/message")
async def get_message(
    user_id: str = Query(..., description="User ID của người dùng"),
    question: str = Query(..., description="Câu hỏi của người dùng"),
):
    """Legacy endpoint - use /chat instead"""
    try:
        request = ChatRequest(user_id=user_id, question=question)
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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)