from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from agno.agent import Message
from typing import Optional
from src.chatbot import agent
from src.chatbot_1 import router_agent
import os, shutil
import json

app = FastAPI(title="Flight Agent API", version="1.0.0")

# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sky-shifters.vercel.app"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Data model
class ChatInput(BaseModel):
    message: str
    access_token: Optional[str] = None  
    user_id: str 
    session_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is my upcoming flight?",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user_id": "1",
                "session_id": "1"
            }
        }

# ✅ Health check endpoint
@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "ok"}

# ✅ Main chat endpoint with proper status codes
@app.post("/chat")
async def chat_handler(data: ChatInput):
    message = data.message
    token = data.access_token
    user_id = data.user_id
    session_id = data.session_id

    if not message:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "response": {
                    "type": "no_tool_call",
                    "success": False,
                    "message": "Message is required",
                    "login": False,
                    "data": None
                }
            }
        )

    msg = Message(
        role="user",
        content=message + (f" my_access token : {token}" if token else ""),
        context={"access_token": token} if token else {}
    )

    try:
        response = router_agent.run(msg, user_id=user_id, session_id=session_id)
        raw = response.content.strip()

        if raw.startswith("```json"):
            raw = raw[len("```json"):].strip()
        elif raw.startswith("```"):
            raw = raw[len("```"):].strip()

        if raw.endswith("```"):
            raw = raw[:-3].strip()

        parsed = json.loads(raw)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"response": parsed}
        )

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "response": {
                    "type": "json_error",
                    "success": False,
                    "message": "Please enter your request again.",
                    "login": False,
                    "data": None
                }
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "response": {
                    "type": "error",
                    "success": False,
                    "message": "An unexpected error occurred, please try again later.",
                    "login": False,
                    "data": None
                }
            }
        )
