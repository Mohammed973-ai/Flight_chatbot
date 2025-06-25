from fastapi import FastAPI, Request
from pydantic import BaseModel
from agno.agent import Message
from src.chatbot import agent
import json

app = FastAPI(title="Flight Agent API", version="1.0.0")

class ChatInput(BaseModel):
    message: str
    access_token: str
    user_id :str
    session_id:str
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

    if not message:
        return {
  "response": {
    "type": "no_tool_call",
    "success": False,
    "message": "Message is required",
    "data" : None
  }
}


    msg = Message(
        role="user",
        content=message + " my_access token :  " + data.access_token,
        context={"access_token": token}
    )

    try:
        response = agent.run(msg, user_id=data.user_id, session_id=data.session_id)
        parsed = json.loads(response.content)
        return {"response": parsed}

    except json.JSONDecodeError:
        return {
            "response": {
                "type": "json_error",
                "success": False,
                "message": "please enter your request again..",
                "data":None
            }
        }

    except Exception as e:
        return {
            "response": {
                "type": "error",
                "success": False,
                "message": "An unexpected error occurred, plaeas try again later..",
                "data":None
            }
        }
