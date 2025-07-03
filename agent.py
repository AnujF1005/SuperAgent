from response_parser import ContentType, parse_ai_response
from tools import TOOLS_DICT
from tools.terminal_session import TerminalSession
from prompt import PromptManager
from context_manager.context_manager import ContextManager
import os

class Agent:
    def __init__(self, llm, working_directory):
        self.llm = llm
        self.working_directory = os.path.abspath(working_directory)
        os.makedirs(self.working_directory, exist_ok=True)        
        self.prompt_manager = PromptManager(
            os="Ubuntu",
            shell="Bash",
            current_working_directory=self.working_directory,
        )
        self.history = []
        
        self.terminal_session = None
        
        self.tool_instances = {}
        for name, ToolClass in TOOLS_DICT.items():
            self.tool_instances[name] = ToolClass()

        os.chdir(self.working_directory)

        self.ctxt_manager = ContextManager(
            llm=self.llm
        )
    
    def cleanup(self):
        if self.terminal_session:
            self.terminal_session.cleanup()
            self.terminal_session = None
        
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
        params_list = list(params.keys())

        if tool_name not in self.tool_instances:
            return f"Tool '{tool_name}' not found."

        tool_executable = self.tool_instances[tool_name]
        
        if tool_name == "shell":
            if not self.terminal_session:
                self.terminal_session = TerminalSession(self.working_directory)
            return tool_executable(**params, terminal_session=self.terminal_session)

        # Validate parameters
        expected_params = TOOLS_DICT[tool_name].params["required"] if hasattr(TOOLS_DICT[tool_name], 'params') else []
        if not all(p in params_list for p in expected_params):
            return f"Missing or extra parameter for tool: {tool_name}. Expected: {expected_params}, Got: {params_list}"

        return tool_executable(**params)

    def invoke(self, query: str):
        if query.strip() == "":
            return
        # print(f"User: {query}")

        prompt = self.prompt_manager.get_prompt(self.history)
        self.ctxt_manager.add_message({
            "type": "system",
            "content": prompt
        })
        self.ctxt_manager.add_message({
            "type": "user",
            "content": query
        })

        print(f"\n >>> USER:\n{query}\n")

        try:
            while True:
                current_context = self.ctxt_manager.get_context()
                response = self.llm.invoke(current_context)
                print("=== >>> USAGE <<< ===")
                print(f"Input tokens:  {response.usage_metadata.get('input_tokens', -1)}")
                print(f"Output tokens: {response.usage_metadata.get('output_tokens', -1)}")
                print(f"Total tokens:  {response.usage_metadata.get('total_tokens', -1)}")
                print(f"Cache Read:    {response.usage_metadata.get('input_token_details', {}).get('cache_read', -1)}")
                print(f"Reasoning:     {response.usage_metadata.get('output_token_details', {}).get('reasoning', -1)}")
                print("=== >>> ===== <<< ===")
                response = response.content
                print(f"\n >>> AGENT:\n{response}\n")
                tool_calls = []
                text_content = ""

                content_blocks = parse_ai_response(response)

                tool_response = ""
                is_tool_invoked = False
                is_task_completed = False
                for content_block in content_blocks:
                    if content_block["type"] == ContentType.TOOL_CALL:
                        tool_calls.append({
                            "tool_name": content_block["tool"],
                            "args": content_block["params"]
                        })
                        if not is_tool_invoked:
                            is_tool_invoked = True
                            # tool_response += "Result of tool invocation:\n\n"

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
                    elif content_block["type"] == ContentType.TEXT_CHUNK:
                        text_content += content_block["content"] + "\n\n"
                
                self.ctxt_manager.add_message({
                    "type": "ai",
                    "content": text_content.strip(),
                    "tool_calls": tool_calls
                })

                # Empty tool_response
                if "" == tool_response.strip():
                    print(f"Agent: {response}\n")
                    print("Empty tool response!!!")
                    tool_response = input("User: ")
                    self.ctxt_manager.add_message({
                        "type": "user",
                        "content": tool_response.strip()
                    })
                else:
                    self.ctxt_manager.add_message({
                        "type": "tool",
                        "content": tool_response.strip()
                    })

                print(f"\n >>> TOOL RESPONSE:\n{tool_response}\n")

                # print(f"\n >>> CURRENT CONTEXT:\n{self.ctxt_manager.get_context()}\n")
                
                print("\n\n"+ "="*50 + "\n\n")
                if is_task_completed:
                    print("Task completed!")
                    print("Exiting...")
                    self.cleanup() # Call cleanup before breaking
                    break
        except KeyboardInterrupt:
            print("\n\nKeyboardInterrupt detected. Exiting gracefully...")
            self.cleanup()
            self.ctxt_manager.print_status()
