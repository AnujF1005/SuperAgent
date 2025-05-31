class AskUserTool:
    name = "ask_user"
    params = ["question"]
    description = """
    Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.
    Parameters:
    - question: (required) The question to ask the user. This should be a clear, specific question that addresses the information you need.
    Usage:
    <ask_user>
    <question>Your question here</question>
    </ask_user>
    """
    examples = """
    Asking user about followup question about given task

    <ask_user>
    <question>Do you want to use OpenAI or Gemini LLM or any other LLM?</question>
    </ask_user>
    """

    def __call__(self, question: str):
        print(f"Agent asking: {question}")
        ans = input(">> ")
        return ans
    
class AttemptCompletionTool:
    name = "attempt_completion"
    params = ["result"]
    description = """
    After each tool use, the user will respond with the result of that tool use, i.e. if it succeeded or failed, along with any reasons for failure. Once you've received the results of tool uses and can confirm that the task is complete, use this tool to present the result of your work to the user. Optionally you may provide a CLI command to showcase the result of your work. The user may respond with feedback if they are not satisfied with the result, which you can use to make improvements and try again.
    IMPORTANT NOTE: This tool CANNOT be used until you've confirmed from the user that any previous tool uses were successful. Failure to do so will result in code corruption and system failure. Before using this tool, you must ask yourself in <thinking></thinking> tags if you've confirmed from the user that any previous tool uses were successful. If not, then DO NOT use this tool.
    Parameters:
    - result: (required) The result of the task. Formulate this result in a way that is final and does not require further input from the user. Don't end your result with questions or offers for further assistance.
    Usage:
    <attempt_completion>
    <result>
    Your final result description here
    </result>
    </attempt_completion>
    """
    examples = """
    Present result of task to user

    <attempt_completion>
    <result>
    Output of newly written algorithm:
    Sum of two values = 10
    Command to reproduce result:
    python main.py
    </result>
    </attempt_completion>
    """

    def __call__(self, result: str):
        print("Agent completed the given task.")
        print(f"Result:\n{result}")

        # Ask user about satisfaction
        ip = input("Are you satisfied?(y/n)\n>> ")
        if ip.lower() == "y":
            return {"user_satisfied": True, "content": result}
        else:
            ip = input("Give Feedback: ")
            return {"user_satisfied": False, "content": result + "\n\nFeedback: " + ip}