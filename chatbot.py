from agno.agent import Agent
from agno.models.groq import Groq 
from agno.memory.v2.db.sqlite import SqliteMemoryDb 
from agno.memory.v2.memory import Memory 
from dotenv import load_dotenv 
from agno.storage.sqlite import SqliteStorage 
from src.helper import *
from instructions import Instructions
from agno.models.google import Gemini
from agno.models.groq import Groq
import os
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
memory_db = SqliteMemoryDb(table_name="users_memory", db_file="tmp/User_preferences_memory.db")
memory = Memory(db=memory_db) # user prefernces memory
storage =SqliteStorage(table_name="agent_sessions", db_file="tmp/session_memory.db")
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
    instructions=Instructions,            # system prompt / persona
    # UX Config
    show_tool_calls=True,                 # logs tool calls (debug/friendly)
    markdown=False                        # disables markdown output formatting
)

# user_id= "1"
# session_id="1"
# # agent.print_response("what is 2+2",
# #                      session_id=session_id,user_id=user_id)
# agent.print_response("I want to searrch aflights from cairo to dubai on 10 july 2025 dont ask for any confirmation do your assumtion",
#                      session_id=session_id,user_id=user_id)
# agent.print_response("""{"message" : "I want to cancel a flight",
#                       "access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODM3YzM1NzRiOTMxM2FmMjViNTRlMWYiLCJlbWFpbCI6ImhvcmVqMTYxNDBAb2Z1bGFyLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaWF0IjoxNzUwMzYxMzg1LCJleHAiOjE3NTA0NDc3ODV9.gltzYMGGxLFF5-DBxxepyC0IzZCTEF_BVE2sVjjWmrQ"}""",
#                      session_id=session_id,user_id=user_id)
# agent.print_response("cancel XA240016",
#                      session_id=session_id,user_id=user_id)
# agent.print_response("Pretty little baby , hellooooo",
#     session_id="1",user_id="1")