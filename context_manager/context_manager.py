import uuid

class ContextManager:
    COMPRESSION_PROMPT = """
    You are a context summarizer for an AI agent. Your task is to take a verbose AI message and condense it to its essential parts, retaining all critical information, instructions, and data.

    RULES:
    1.  Do NOT change or omit any code blocks, file paths, or specific data values.
    2.  Remove conversational filler (e.g., "Okay, I will now...", "Here is the result...").
    3.  Condense long explanations into concise points.
    4.  Focus on the *conclusion* or *decision* the AI made.
    5.  The output must be a concise summary of the original message.
    6.  Do NOT include any additional text like "Here is the summary" or "The AI said" or similar phrases.

    Original Message:
    ---
    {original_ai_message}
    ---
    """

    CHECK_TOOL_SUCCESS_PROMPT = """
    You are a tool execution evaluator. Your task is to determine if a tool execution was successful based on given tool call and its response. Your response should be a simple "yes" or "no".
    Don't include any additional text or explanations.

    RULES:
    1.  A tool execution is considered successful if it returns the expected result or completes the task it was designed for.
    2.  If the tool call contains respond from USER, it is always considered successful.

    Tool Call:
    ---
    {tool_call}
    ---
    Tool Response:
    ---
    {tool_response}
    ---
    """

    IS_GOAL_ACHIEVED_PROMPT = """
    You are a helper for an LLM based agent. In agent environments, the requested tool call by an agent may not always succeed. In such cases, the agent retries the tool call with different attributes or parameters or content
    or even use a different tool or mix of different tools to achieve the same goal. I will give you a back and forth conversation between an AI agent and a tool execution which can contain multiple tool calls and responses.
    Generally, the first tool call request gives the intent of the tool call and the subsequent tool calls are retries or attempts to achieve the same goal. The last tool execution response will always be the successful one.
    Your task is to determine if the goal of the agent was achieved by the last tool call or it is half done and needs further tool calls to achieve the goal.
    Your response should be a simple "yes" or "no", where "yes" meaning goal is completed and "no" meaning goal is not completed and more tool calls may be required.
    Do not include any additional text or explanations.

    Conversation:
    ---
    {conversation}
    ---
    """

    def __init__(self, llm, compress_on_add: bool = True):
        self.llm = llm
        self.compress_on_add = compress_on_add
        self.context_history = {} # Stores messages in the format {id: message_dict}
        # Stores (ai_msg_id, failed_tool_call_id) that need to be resolved
        self.pending_failed_tool_calls = []
        self.uncompressed_tokens = 0
        self.compressed_tokens = 0
        self._last_message_id = None

    def __del__(self):
        """Cleanup method to ensure no memory leaks."""
        self.context_history.clear()
        self.pending_failed_tool_calls.clear()

        self.print_status()

    def _generate_message_id(self) -> str:
        return f"msg_{uuid.uuid4().hex[:8]}"

    def _compress_content(self, content: str) -> str:
        """Uses an LLM to compress the content of an AI message."""
        if not self.compress_on_add or content.strip() == "":
            return content
        prompt = self.COMPRESSION_PROMPT.format(original_ai_message=content)
        # Assuming your LLM library has a simple invocation method
        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def _is_tool_execution_successful(self, tool_call: str, tool_response: str) -> bool:
        """Determines if a tool execution was successful based on its response."""
        prompt = self.CHECK_TOOL_SUCCESS_PROMPT.format(tool_call=tool_call, tool_response=tool_response)
        response = self.llm.invoke(prompt)
        return response.content.strip().lower() == "yes"
    
    def _is_goal_achieved(self, conversation: str) -> bool:
        """Determines if the goal of the agent was achieved based on the conversation."""
        prompt = self.IS_GOAL_ACHIEVED_PROMPT.format(conversation=conversation)
        response = self.llm.invoke(prompt)
        return response.content.strip().lower() == "yes"

    def add_message(self, message: dict):
        """Adds a new message to the context, processing it based on type."""
        msg_id = self._generate_message_id()
        msg_type = message["type"]
        original_content = message["content"]
        
        new_message = {
            "id": msg_id,
            "type": msg_type,
            "original_content": original_content,
            "compressed_content": original_content, # Default
            "metadata": {}
        }

        if msg_type == "system" or msg_type == "user":
            # Keep as is
            pass

        elif msg_type == "ai":
            new_message["compressed_content"] = self._compress_content(original_content)
            if message.get("tool_calls"):
                new_message["metadata"]["tool_call"] = message["tool_calls"][0] # Assuming one for simplicity TODO: Handle multiple tool calls if needed

        elif msg_type == "tool":
            # This logic assumes the tool response is for the IMMEDIATELY preceding AI message.
            # A more robust system would use IDs to link them explicitly.
            last_ai_message = None
            if self._last_message_id is not None and self.context_history[self._last_message_id]["type"] == "ai":
                last_ai_message = self.context_history[self._last_message_id]
            
            if last_ai_message:
                is_successful = self._is_tool_execution_successful(self._tool_string(last_ai_message["metadata"]["tool_call"]), original_content)
                last_ai_message["metadata"]["tool_successful"] = is_successful
                new_message["metadata"]["is_response_to"] = last_ai_message["id"]

                if not is_successful:
                    # Mark the previous AI call as a pending failure
                    self.pending_failed_tool_calls.append((last_ai_message["id"], msg_id))
                elif len(self.pending_failed_tool_calls) > 0:
                    # Check if the last tool call resolved any pending failures
                    conversation = ""
                    for (ai_id, tool_id) in self.pending_failed_tool_calls:
                        if ai_id in self.context_history:
                            conversation += f"AI:\n{self.context_history[ai_id]['compressed_content']}\n"
                            # Include tool call details as well
                            if self.context_history[ai_id].get("metadata", {}).get("tool_call"):
                                tool_call = self.context_history[ai_id]["metadata"]["tool_call"]
                                conversation += f"\n{self._tool_string(tool_call)}\n"
                        if tool_id in self.context_history:
                            conversation += f"Tool Response:\n{self.context_history[tool_id]['original_content']}\n"
                    
                    # Add current tool response and its corresponding ai message to the conversation
                    conversation += f"AI:\n{last_ai_message['compressed_content']}\n"
                    # Include tool call details as well
                    if last_ai_message.get("metadata", {}).get("tool_call"):
                        tool_call = last_ai_message["metadata"]["tool_call"]
                        conversation += f"\n{self._tool_string(tool_call)}\n"
                    conversation += f"Tool Response:\n{original_content}\n"
                    
                    # Check if the goal was achieved
                    if self._is_goal_achieved(conversation):
                        # Remove all pending failures without removing first ai message.
                        to_delete_ids = []
                        for i, (ai_id, tool_id) in enumerate(self.pending_failed_tool_calls):
                            if i != 0: # Skip the first ai message
                                to_delete_ids.append(ai_id)
                            to_delete_ids.append(tool_id)
                        
                        # Remove all messages with IDs in to_delete_ids
                        for id in to_delete_ids:
                            if id in self.context_history:
                                del self.context_history[id]
                        
                        # Clear the pending failed tool calls
                        self.pending_failed_tool_calls.clear()
                    else:
                        self.pending_failed_tool_calls.append((last_ai_message["id"], msg_id))
                        
        self.context_history[msg_id] = new_message
        # Update token counts
        self.uncompressed_tokens += len(original_content.split())
        self.compressed_tokens += len(new_message["compressed_content"].split())
        # Update the last message ID
        self._last_message_id = msg_id

    def _tool_string(self, tool_call: dict) -> str:
        """Formats a tool call for display."""
        tool_name = tool_call["tool_name"]
        args = "\n".join(f"<{k}>{v}</{k}>" for k, v in tool_call.get("args", {}).items())
        return f"<{tool_name}>\n{args}\n</{tool_name}>"
    
    def get_context(self) -> str:
        """Constructs the final context string from the processed history."""
        full_context = []
        for msg_id, msg in self.context_history.items(): # In Python 3.7 and later, this iteration preserves the insertion order of the key-value pairs.
            # Simple formatting, can be customized for specific models
            role = msg['type'].capitalize()
            if role == "Ai": role = "Assistant"
            if role == "Tool": role = "Tool Response"

            full_context.append(f"{role}:\n{msg['compressed_content']}")

            # If this is an AI message with a tool call, append the tool call string
            if role == "Assistant" and msg.get("metadata", {}).get("tool_call"):
                tool_call = msg["metadata"]["tool_call"]
                tool_string = self._tool_string(tool_call)
                full_context.append(tool_string)
        
        return "\n\n".join(full_context)

    def __str__(self):
        return self.get_context()
    
    def print_status(self):
        """Prints the current status of the context manager."""
        print(f"Context Manager Status:")
        print(f"Total Messages: {len(self.context_history)}")
        print(f"Pending Failed Tool Calls: {len(self.pending_failed_tool_calls)}")
        print(f"Uncompressed Tokens: {self.uncompressed_tokens}")
        print(f"Compressed Tokens: {self.compressed_tokens}")