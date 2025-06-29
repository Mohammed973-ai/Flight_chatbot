from fastapi import FastAPI, Request
from pydantic import BaseModel
from agno.agent import Message
from typing import Optional
from src.chatbot import agent
import re
import json

app = FastAPI(title="Flight Agent API", version="1.0.0")

class ChatInput(BaseModel):
    message: str
    access_token: Optional[str] = None  
    user_id: str 
    session_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": """What is my upcoming flight? responde in json like this:
                { 'type' : 'search_flight', or 'booked_flight',or 'cancel_flight',or 'change_user_password',or 'request_password_reset',or 'reset_password_with_code',or 'no_tool_call'
                  'success' : True(boolean)| False(boolean)(in case of exception)
                  'message' : 'type your reply to the user here',
                  'data': in case you called search_flight tool put the json response that is in the "data" here
                }
DONT TYPE ANY INTRODUCTORY SENTENCES,IF YOU WANT TO TALK /CHAT WITH USER YOU HAVE TO PUT IT IN "message" IN JSON RESPONSE..""",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user_id": "1",
                "session_id": "1"
            }
        }
@app.post("/chat")
async def chat_handler(data: ChatInput):
    message = data.message
    token = data.access_token
    user_id = data.user_id

    if not message:
        return {
            "response": {
                "type": "no_tool_call",
                "success": False,
                "message": "Message is required",
                "login":False,
                "data": None
            }
        }

    msg = Message(
        role="user",
        content=message + (f" my_access token : {token}" if token else "")+",responde in json like this:\n{ 'type' : 'search_flights', or 'booked_flight',or 'cancel_flight',or 'change_user_password',or 'request_password_reset',or 'reset_password_with_code',or 'no_tool_call',or'update_uer_profile',or 'customer_service'\n  'success' : True(boolean)| False(boolean)(in case of exception)\n 'message' : 'type your reply to the user here',\n \"login\":True (in case the tool you use need an access token and it is not provided) |False (in case the access token is provided or the tool doesnt need access_token) \n'data':  the api flights search json response from amadeus if doesnt exist put null.",
        context={"access_token": token} if token else {}
    )

    try:
        response = agent.run(msg, user_id=user_id, session_id=data.session_id)
        raw = response.content.strip()
        if raw.startswith("```json"):
            raw = raw[len("```json"):].strip()
        elif raw.startswith("```"):
            raw = raw[len("```"):].strip()

        if raw.endswith("```"):
            raw = raw[:-3].strip()

        parsed = json.loads(raw)
        return {"response": parsed}

    except json.JSONDecodeError:
        return {
            "response": {
                "type": "json_error",
                "success": False,
                "message": "Please enter your request again.",
                "login":False,
                "data": None
            }
        }

    except Exception as e:
        

        return {
            "response": {
                "type": "error",
                "success": False,
                "message": f"An unexpected error occurred, please try again later..",
                "login":False,
                "data": None
            }
        }