import fastapi
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form

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
        with open(f"./history/{user_id}.json", 'r') as f:
            history = f.read()
    except FileNotFoundError:
        return None
    return history


@app.post('/get_chat_conv')
async def post_session(
    phoneNumber: str = Form(...),
):
    data = load_history(user_id=phoneNumber)
    return data