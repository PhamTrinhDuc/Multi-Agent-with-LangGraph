import fastapi
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form
from fastapi import Query
import json
from main import response_chatbot
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def load_history(user_id: str):
    try:
        with open(f"./history/{user_id}.json", 'r', encoding='utf-8') as f:
            try:
                history = json.load(f)
                return history
            except json.JSONDecodeError:
                return []
    except FileNotFoundError:
        return []

@app.get("/conversation")
async def get_session(user_id: str = Query(...)):
    data = load_history(user_id=user_id)
    return data

# uvicorn.run(app=app, host="127.0.0.1", port="8000", reload=True)

# To run the FastAPI application, use the following command in the terminal:
# Make sure you are in the directory containing `app.py`.

# Command: uvicorn app:app --host 127.0.0.1 --port 8000 --reload
# 

@app.get("/message")
async def get_message(
    user_id: str = Query(..., description="User ID của người dùng"),
    question: str = Query(..., description="Câu hỏi của người dùng"),
):
    try:
        response = response_chatbot(question=question, user_id=user_id)
        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})