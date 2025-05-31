from agent import Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv("../.env")

llm = ChatOpenAI(model="gpt-4o-mini")

ag = Agent(
    llm,
    working_directory="/mnt/d/AI/SuperAgentDash",
)

query = """
Write comments in the code of SuperAgent written in directory /mnt/d/AI/SuperAgentDash
"""

# Invoke the Agent with the specified queryag.invoke(query)