from agent import Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv("../.env")

llm = ChatOpenAI(model="gpt-4o-mini")


ag = Agent(
    llm,
    working_directory="/mnt/d/AI/SuperAgent",
)

query = """
Improve LLM Agent written at location /mnt/d/AI/SuperAgent by refactoring the code and adding comments.
"""

ag.invoke(query)