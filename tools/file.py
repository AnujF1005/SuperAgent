import os
import re

MAX_READ_FILE_LINES_LIMIT = 2000

class WriteToFileTool:
    name = "write_to_file"
    params = {
        "required": ["path", "content"],
        "optional": []
    }
    description = """
    Request to write content to a file at the specified path. If the file exists, it will be overwritten with the provided content. If the file doesn't exist, it will be created. This tool will automatically create any directories needed to write the file.
    Parameters:
    - path: (required) The path of the file to write to (relative to the current working directory)
    - content: (required) The content to write to the file. ALWAYS provide the COMPLETE intended content of the file, without any truncation or omissions. You MUST include ALL parts of the file, even if they haven't been modified.
    Usage:
    <write_to_file>
    <path>File path here</path>
    <content>
    Your file content here
    </content>
    </write_to_file>
    """
    examples = """
    Requesting to create a new file

    <write_to_file>
    <path>src/frontend-config.json</path>
    <content>
    {
    "apiEndpoint": "https://api.example.com",
    "theme": {
        "primaryColor": "#007bff",
        "secondaryColor": "#6c757d",
        "fontFamily": "Arial, sans-serif"
    },
    "features": {
        "darkMode": true,
        "notifications": true,
        "analytics": false
    },
    "version": "1.0.0"
    }
    </content>
    </write_to_file>
    """

    def __call__(self, path: str, content: str):
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as file:
            file.write(content)
        
        return f"New file created: {path} and written successfully." # No need to return the content, as it is already present in the context of the agent.

class ReadFileTool:
    name = "read_file"
    params = {
        "required": ["path"],
        "optional": ["start_line_index", "lines_to_read"]
    }
    description = """
    Request to read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file you do not know the contents of, for example to analyze code, review text files, or extract information from configuration files. Automatically extracts raw text from PDF and DOCX files. May not be suitable for other types of binary files, as it returns the raw content as a string.
    Optionally you can also provide start line index from where to start reading the file and number of lines to read. NOTE: this tool can't read more than 2000 lines at once from a file.
    Parameters:
    - path: (required) The path of the file to read (relative to the current working directory)
    - start_line_index: (optional) (int) line index to start reading file from.
    - lines_to_read: (optional) (int) number of lines to read from start_line_index. If not mentioned, all lines will be read from file.
    Usage:
    <read_file>
    <path>File path here</path>
    </read_file>
    """
    examples = """
    Requesting to read a whole file src/main.py

    <read_file>
    <path>src/main.py</path>
    </read_file>

    Requesting to read a file src/data.py from line index 3000 and read 100 lines
    <read_file>
    <path>src/data.py</path>
    <start_line_index>3000</start_line_index>
    <lines_to_read>100</lines_to_read>
    </read_file>
    """
    def _parse_inputs(self, input_dict: dict):
        input_dict['start_line_index'] = int(input_dict.get('start_line_index', 0))
        input_dict['lines_to_read'] = int(input_dict.get('lines_to_read', -1))
        return input_dict

    def __call__(self, **kwargs):
        """
        Arguments expected in kwargs:
        - path: (required) The path of the file to read (relative to the current working directory)
        - start_line_index: (optional) (int) line index to start reading file from.
        - lines_to_read: (optional) (int) number of lines to read from start_line_index. If not mentioned, all lines will be read from file.
        """
        # Parse inputs
        parsed_inputs = self._parse_inputs(kwargs)

        path = parsed_inputs["path"]
        start_line_index = parsed_inputs.get("start_line_index", 0)
        lines_to_read = parsed_inputs.get("lines_to_read", -1)
        
        if not os.path.exists(path):
            return f"File at path {path} does not exist"
        
        if start_line_index < 0:
            return f"ERROR: Negative start_line_index"

        file_content = ""
        with open(path, 'r') as file:
            file_content = file.read()

        lines = file_content.split('\n')

        if start_line_index > 0:
            lines = lines[start_line_index:]

        if lines_to_read > 0:
            lines = lines[:lines_to_read]

        total_lines = len(lines)

        if total_lines > MAX_READ_FILE_LINES_LIMIT:
            lines = lines[:MAX_READ_FILE_LINES_LIMIT]
        
        file_content = '\n'.join(lines)
        if total_lines > MAX_READ_FILE_LINES_LIMIT:
            file_content += " ... (truncated)"

        return f"Content of file {path}:\n" + file_content

class ReplaceInFileTool:
    name = "replace_in_file"
    params = {
        "required": ["path", "search_block", "replace_block"],
        "optional": []
    }
    description = """
    Request to replace sections of content in an existing file using SEARCH and REPLACE blocks that define exact changes to specific parts of the file. This tool should be used when you need to make targeted changes to specific parts of a file.
    Parameters:
    - path: (required) The path of the file to modify (relative to the current working directory)
    - search_block: (required) Exact block content to be replaced from the file.
    - replace_block: (required) New content to replace with.

    Critical rules:
    1. search_block must match the associated file section to find EXACTLY:
        * Match character-for-character including whitespace, indentation, line endings
        * Include all comments, docstrings, etc.
    2. This tool will ONLY replace the first match occurrence.
        * Call this tool multiple times if you need to make multiple changes.
        * Include *just* enough lines in each SEARCH section to uniquely match each set of lines that need to change.
    3. Keep search_block and replace_block concise.
    4. Don't add any newline (`\n`) or extra space (` `) at start or end of search_block and replace_block if it is not supposed to be part of the current or updated file.
    4. Special operations: To delete code, use empty replace_block.
    Usage:
    <replace_in_file>
    <path>File path here</path>
    <search_block>Content to be replace with</search_block>
    <replace_block>New content here</replace_block>
    </replace_in_file>
    """
    examples = """
    Requesting to make targeted edits to a file

    <replace_in_file>
    <path>src/components/App.py</path>
    <search_block>import os</search_block>
    <replace_block>import subprocess</replace_block>
    </replace_in_file>

    <replace_in_file>
    <search_block>def handleSubmit() {
    saveData();
    setLoading(false);
    }</search_block>
    <replace_block></replace_block>
    </replace_in_file>
    """

    def __call__(self, path: str, search_block: str, replace_block: str) -> str:
        # --- 1. Input Validation ---
        if not path or not isinstance(path, str):
            return f"ERROR: Path parameter is missing or invalid. Path provided: '{str(path)}'."
        if not isinstance(search_block, str): # search_block must be a string, even if empty
            return f"ERROR: search_block parameter must be a string. Path: '{path}'."
        if not isinstance(replace_block, str): # replace_block must be a string, even if empty
            return f"ERROR: replace_block parameter must be a string. Path: '{path}'."

        # --- 2. File System Checks ---
        if not os.path.exists(path):
            return f"ERROR: File not found at path: {path}"
        if not os.path.isfile(path):
             return f"ERROR: Path is not a file: {path}"

        # --- 3. Read Original File Content ---
        try:
            with open(path, 'r', encoding='utf-8') as file:
                original_content = file.read()
        except Exception as e:
            return f"ERROR: Error reading file {path}: {str(e)}"

        # --- 4. Handle Empty/Whitespace-Only Diff ---
        if not search_block.strip():
            return f"search block is empty, so no modifications made to file {path}"

        # --- 6. Apply Changes ---
        match_start_index = -1
        match_end_index = -1

        # Attempt 1: Exact match
        exact_index = original_content.find(search_block)
        if exact_index != -1:
            match_start_index = exact_index
            match_end_index = exact_index + len(search_block)
        
        if match_start_index != -1:
            # Reconstruct the content with the replacement
            modified_content = (
                original_content[:match_start_index] +
                replace_block +
                original_content[match_end_index:]
            )
        else:
            # If no match found for a search_block, it's an error
            return f"ERROR: search_block did not find a match in file {path}"

        # --- 7. Process Results and Write File if Changed ---
        try:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(modified_content)
            return f"File {path} updated successfully."
        except Exception as e:
            return f"ERROR: Error writing updated content to file {path}: {str(e)}. In-memory changes were not saved."
