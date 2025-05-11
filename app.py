from agno.agent import Agent
from agno.models.groq import Groq 
from agno.memory.v2.db.sqlite import SqliteMemoryDb 
from agno.memory.v2.memory import Memory 
from dotenv import load_dotenv 
from agno.storage.sqlite import SqliteStorage 
from src.helper import search_flights
import os
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
memory_db = SqliteMemoryDb(table_name="memory", db_file="tmp/memory.db")
memory = Memory(db=memory_db) # user prefernces memory
# memory.clear()
agent = Agent(model = Groq(id = "qwen-qwq-32b",          
                           api_key=groq_key),
         add_history_to_messages=True,# built-in message/short-term
         storage=SqliteStorage(table_name="agent_sessions", db_file="tmp/data.db"), # persistent memory/long-term 
         memory=memory, # user prefernces memory
         enable_agentic_memory=True, # If true, enables the agent to manage the user’s memory (user prefernces memory)
         show_tool_calls=True,
         markdown=True,
         enable_session_summaries=True, # summary memory
         enable_user_memories=True,#If true, create and store personalized memories for the user.user prefernces memory
         tools=[search_flights],
         instructions=["""you are a helpful flight search assistant ,
                    #    "if user asked you any unrelated topic **politly** tell them that you cant,
                    when user ask for a flight search you **MUST** call the tool each time and dont depend on your memory when user asking for search
                    # "if they gave you missing information ask only for those missing info",
                    # "the mandatory info that you need are source,distination,departure data",if user didnt provide them
                    **politly** ask for them
                    #   "**DONT ASK USER ANY FEATURES OTHER THAN THE MANDATORY AS LONG AS THEY DIDNT PROVIDE IT**","you will get from the flight search tool a dictionary with full details and nice output representation the nice output to the user and save the dictionary so when they ask you about some details, the dictionary can help you answer """]
         )
# ------------------------------------------------------------------
#  builtin(short term) / prisistant (longterm) meomry
# ------------------------------------------------------------------
# agent.print_response("Do you remeber my name",
#                      user_id = "user_1",session_id="sess1")#--> last line
# agent.print_response("my name is Ahmed I love eating",
#                     user_id = "user_1",session_id="sess1")
# agent.print_response("Do you remeber my name",
#                      user_id = "user_1",session_id="sess1")
# agent.print_response("do you know what I love? ",
#                      user_id = "user_1",session_id="sess2")
# ---------------------------------------------------------------------
#                           user-prefernces
# ----------------------------------------------------------------------
# agent.print_response(
#     "My name is John Doe and I like to hike in the mountains on weekends.",
#     stream=True,
#     user_id="user_1",
# )
# agent.print_response("What are my hobbies?", stream=True, user_id="user_1")

# # The agent can also remove all memories from the user's memory
# agent.print_response(
#     "Remove all existing memories of me. Completely clear the DB.",
#     stream=True,
#     user_id="user_1"
# )
# -----------------------------------------------------------------------------
# Testing
# -----------------------------------------------------------------------------
# agent.get_messages_for_session()
# read_tool_call_history=True
# *-*--*--*-*-*-*-*-*-*-*-*-*-*-*-*-
session_id="session_1"
user_id = "user_1"
# agent.print_response("what is 2+2",
#                      session_id=session_id,user_id=user_id) # unrelated topic
# agent.print_response("I want to search a flight to dubai on 10day/6/2025",
#                      session_id=session_id,user_id=user_id)
# agent.print_response("I want to searrch aflights from cairo to dubai on 10 june 2025 dont ask for any confirmation do your assumtion",
#                      session_id=session_id,user_id=user_id)
# agent.print_response("sort the flights descendingly according to price",
#                      session_id=session_id,user_id=user_id)
agent.print_response("does any of those has no stops and show me number of stops for each flight",session_id=session_id,user_id=user_id)
# agent.print_response("I always love high price flights",
#                      session_id=session_id,user_id=user_id)
# print(agent.get_messages_for_session(session_id="session_1",user_id="user_1"))