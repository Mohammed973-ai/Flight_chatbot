from agno.agent import Agent
from agno.models.groq import Groq 
from agno.memory.v2.db.sqlite import SqliteMemoryDb 
from agno.memory.v2.memory import Memory 
from dotenv import load_dotenv 
from agno.storage.sqlite import SqliteStorage 
from src.helper import *
from src.instructions import Instructions
from src.instructions_1 import *
from agno.models.groq import Groq
from agno.models.google import Gemini
from agno.team import Team
import os
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")
memory_db = SqliteMemoryDb(table_name="users_memory", db_file="tmp/User_preferences_memory.db")
memory = Memory(db=memory_db) # user prefernces memory
storage =SqliteStorage(table_name="agent_sessions", db_file="tmp/session_memory.db")
flight_tools = [search_flights, booked_flight, cancel_flight]
user_tools = [change_user_password, request_password_reset, reset_password_with_code,update_user_profile]
general_tools = [customer_service]
flight_agent = Agent(
         name = "flight_agent",
         role = "handle flight services like search_flights,or cancel flights and check for booked flights",
     model=Groq(id = "qwen-qwq-32b",api_key=groq_key),
     instructions=flight_instructions,
     tools =flight_tools,
     show_tool_calls=False

)
user_agent = Agent(
    name= "user_agent",
    role = "handle user services like change_user_password,request_password_reset, reset_password_with_code,update_user_profile",
    model=Groq(id = "qwen-qwq-32b",api_key=groq_key),
    tools = user_tools,
    instructions=user_instructions,
    show_tool_calls=False

)
general_agent = Agent(
    name= "customer_service_and_chat_agent",
    role = "answer any general questions about \
        flights or respond to user if the prompt is general\
              (e.g.HI, how are you)  ",
    model=Groq(id = "qwen-qwq-32b",api_key=groq_key),
    tools = general_tools,
    instructions=cutomer_service_and_chat_instructions,
    show_tool_calls=False

)
router_agent= Team(
    name = "flight_team",
    mode ="route",
    model=Groq(id = "qwen-qwq-32b",api_key=groq_key),
    members=[flight_agent,user_agent,general_agent],
    storage=storage,                      # sesisons Database
    memory=memory,
    add_history_to_messages=True,
    description="you are a router agent that give the user query to the appropriate agent",
    instructions=router_instructions,                       # user preference memory
    enable_agentic_memory=True,           # enables autonomous user memory management
    enable_session_summaries=True,        # summary memory
    # UX Config
    markdown=False,                 # disables markdown output formatting
    show_tool_calls=False,
)