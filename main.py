from agent import Agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import argparse
import os

load_dotenv("../.env")

def invoke_agent(task, working_dir):
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash-lite-preview-06-17")
    llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash-preview-04-17")

    ag = Agent(
        llm,
        working_directory=working_dir,
    )

    try:
        ag.invoke(task)
    finally:
        ag.cleanup()

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Agent Runner")
    
    parser.add_argument("-task", help="Task for agent", required=True)
    parser.add_argument("-wd", help="Working Directory", default=os.getcwd())

    args = parser.parse_args()
    print(args)
    invoke_agent(args.task, args.wd)

    # # For debugging purposes
    # # invoke_agent("Create a python simulation of big bang. Also add slider to control speed of simulation.", "temp")
    # invoke_agent("Go through all the project files and refactor the name of the class ReplaceInFileTool with GitReplaceTool", "SuperAgentRunner")