from response_parser import ContentType, parse_ai_response
from tools import TOOLS_DICT
from prompt import PromptManager

class Agent:
    def __init__(self, llm, working_directory):
        self.llm = llm
        self.prompt_manager = PromptManager(
            os="Ubuntu",
            shell="Bash",
            current_working_directory=working_directory,
        )
        self.history = []
    
    def invoke_tool(self, tool_call: dict):
        tool_name = tool_call["tool"]
        params = tool_call["params"]

        tool_executable = TOOLS_DICT[tool_name]()

        if set(tool_executable.params) != set(params.keys()):
            return "Missing or extra parameter for tool: " + tool_name
        
        return tool_executable(**params)

    def invoke(self, query: str):
        if query.strip() == "":
            return
        print(f"User: {query}")

        prompt = self.prompt_manager.get_prompt(self.history)
        prompt += query

        self.history.append(prompt)

        while True:
            response = self.llm.invoke(prompt)
            response = response.content
            print(f"AI: {response}")
            self.history.append(response)

            content_blocks = parse_ai_response(response)

            tool_response = ""
            is_tool_invoked = False
            is_task_completed = False
            for content_block in content_blocks:
                if content_block["type"] == ContentType.TOOL_CALL:
                    if not is_tool_invoked:
                        is_tool_invoked = True
                        tool_response += "Result of tool invocation:\n\n"

                    if content_block["tool"] == "attempt_completion":
                        tr = self.invoke_tool(content_block)
                        if type(tr) == dict:
                            if tr["user_satisfied"]:
                                is_task_completed = True
                            tool_response += tr["content"] + "\n\n"
                        else:
                            tool_response += tr + "\n\n"
                        break
                    else:
                        tool_response += self.invoke_tool(content_block) + "\n\n"
            
            print(f"Tool Response: {tool_response}")
            self.history.append(tool_response)
            prompt = "\n".join(self.history) + "\n" + tool_response
            
            print("\n\n"+ "="*50 + "\n\n")
            if is_task_completed:
                print("Task completed!")
                print("Exiting...")
                break
            
