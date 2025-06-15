from typing import Union

class ContextManager:
    """
    Manages and optionally compresses conversational context for an Agent or LLM.

    The context is stored in a structured manner and can be transformed to be more LLM-friendly.
    If enabled, context compression uses the provided language model to reduce size while retaining meaning.
    A word-based length limit can also be enforced to keep the context concise. (Token-based limit: TODO)

    Parameters:
        llm: The language model used for compressing context.
        compress (bool): If True, uses the LLM to compress context when needed.
        max_length (int): Maximum allowed context length in words. 0 means no limit.
    """

    def __init__(self, llm, compress=True, max_length=0):
        self.llm = llm
        self.compress = compress
        self.max_length = max_length
        self.context = []
        self.context_length = 0

    def __compress_context(self, text: Union[str, list[str]]) -> None:
        """
        Compresses the given text along with the existing context using the LLM.

        Args:
            text (Union[str, list[str]]): New content to be compressed; can be a single string or a list of strings.
        """
        pass

    def add_to_context(self, text: Union[str, list[str]]) -> None:
        """
        Adds new text to the context. Compresses context if length exceeds max_length.

        If compression is disabled and the context exceeds the allowed length, an error is raised.

        Args:
            text (Union[str, list[str]]): The content to add, as a string or list of strings.
        """
        pass

    def get_context(self) -> str:
        """
        Returns the full context as a single string.

        Returns:
            str: The current stored context.
        """
        pass
