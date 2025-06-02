from agent import Agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import argparse
import os

load_dotenv("../.env")

def invoke_agent(task, working_dir):
    # Change working directory
    os.system(f"cd {working_dir}")
    
    llm = ChatOpenAI(model="gpt-4o-mini")

    ag = Agent(
        llm,
        working_directory=working_dir,
    )

    ag.invoke(task)

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Agent Runner")
    
    parser.add_argument("-task", help="Task for agent", required=True)
    parser.add_argument("-wd", help="Working Directory", default=os.getcwd())

    args = parser.parse_args()
    print(args)
    invoke_agent(args.task, args.wd)