from agno.agent import Agent
from agno.models.groq import Groq 
from agno.memory.v2.db.sqlite import SqliteMemoryDb 
from agno.memory.v2.memory import Memory 
from dotenv import load_dotenv 
from agno.storage.sqlite import SqliteStorage 
from src.helper import *
from src.instructions import Instructions
from agno.models.groq import Groq
from agno.models.google import Gemini
import os
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")
memory_db = SqliteMemoryDb(table_name="users_memory", 
                           db_file="tmp/User_preferences_memory.db")
memory = Memory(db=memory_db) # user prefernces memory
storage =SqliteStorage(table_name="agent_sessions", 
                    db_file="tmp/session_memory.db")
flight_tools = [search_flights, booked_flight, cancel_flight]
user_tools = [change_user_password, request_password_reset, reset_password_with_code,customer_service]
agent = Agent(
    model=Groq(id = "llama-3.3-70b-versatile",api_key=groq_key),
    # Memory Config
    add_history_to_messages=True,         # short-term memory (session memory)
    storage=storage,                      # sesisons Database
    memory=memory,                        # user preference memory
    enable_agentic_memory=True,           # enables autonomous user memory management
    enable_session_summaries=True,        # summary memory
    # Tools & Instructions
    tools=flight_tools + user_tools,      # combined tool list
    instructions=Instructions,    # system prompt / persona
    show_tool_calls=False,
    # UX Config
    markdown=False                        # disables markdown output formatting
)
user_id= "4"
session_id="1"
agent.print_response("I want to search flights from cairo to dubai on 15/7/2025 ",user_id=user_id,session_id=session_id)