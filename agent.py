from response_parser import ContentType, parse_ai_response
from tools import TOOLS_DICT
from tools.browser import SearchTool # Added import
from tools.terminal_session import TerminalSession
from prompt import PromptManager
import os

class Agent:
    def __init__(self, llm, working_directory):
        self.llm = llm
        self.prompt_manager = PromptManager(
            os="Ubuntu",
            shell="Bash",
            current_working_directory=working_directory,
        )
        self.history = []
        # Start persistent visible terminal
        self.terminal_session = TerminalSession(working_directory)
        
        # Instantiate tools
        self.tool_instances = {}
        for name, ToolClass in TOOLS_DICT.items():
            self.tool_instances[name] = ToolClass()
            # Future: If a tool needs specific init args like terminal_session, handle here.
            # For now, SearchTool initializes its driver internally.

        # Change working directory
        os.chdir(working_directory)
    
    def cleanup(self):
        # Cleanup terminal session
        if hasattr(self, "terminal_session") and self.terminal_session:
            self.terminal_session.cleanup()
            self.terminal_session = None
        
        # Cleanup tools
        for tool_name, tool_instance in self.tool_instances.items():
            if hasattr(tool_instance, 'quit_driver') and callable(getattr(tool_instance, 'quit_driver')):
                print(f"Attempting to quit driver for {tool_name}...")
                try:
                    tool_instance.quit_driver()
                except Exception as e:
                    print(f"Error quitting driver for {tool_name}: {e}")
            elif hasattr(tool_instance, 'cleanup') and callable(getattr(tool_instance, 'cleanup')):
                print(f"Attempting to cleanup {tool_name}...")
                try:
                    tool_instance.cleanup()
                except Exception as e:
                    print(f"Error cleaning up {tool_name}: {e}")


    def invoke_tool(self, tool_call: dict):
        tool_name = tool_call["tool"]
        params = tool_call["params"]

        if tool_name not in self.tool_instances:
            return f"Tool '{tool_name}' not found."

        tool_executable = self.tool_instances[tool_name]
        
        # Inject terminal_session for shell tool
        # This specific injection logic might need refinement if more tools need special context
        if tool_name == "shell" and hasattr(tool_executable, '__call__'):
             # Assuming shell tool's __call__ can accept terminal_session
            return tool_executable(**params, terminal_session=self.terminal_session)

        # Validate parameters - this check is against the class definition's params
        # For instantiated tools, we might need to access a 'params' attribute if it's consistently defined
        # Or assume the tool's __call__ method handles param validation.
        # For now, let's assume 'params' is an attribute on the instance or class.
        expected_params = getattr(tool_executable, 'params', []) 
        if set(expected_params) != set(params.keys()):
            # Allow for optional params if not all expected_params are in params.keys()
            # This check needs to be more robust if tools have optional params.
            # A simple check for now:
            if not all(p in expected_params for p in params.keys()):
                 return f"Missing or extra parameter for tool: {tool_name}. Expected: {expected_params}, Got: {list(params.keys())}"
            # If all provided params are in expected_params, but not all expected_params are provided,
            # it implies optional parameters. This part of logic might need adjustment based on tool design.

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
            
            # Empty tool_response
            if "" == tool_response.strip():
                print("Empty tool response!!!")
                tool_response = input("User: ")

            print(f"Tool Response: {tool_response}")
            self.history.append(tool_response)
            prompt = "\n".join(self.history) + "\n" + tool_response
            
            print("\n\n"+ "="*50 + "\n\n")
            if is_task_completed:
                print("Task completed!")
                print("Exiting...")
                self.cleanup() # Call cleanup before breaking
                break
            
