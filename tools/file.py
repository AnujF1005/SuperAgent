import os
import re

class WriteToFileTool:
    name = "write_to_file"
    params = ["path", "contents"]
    description = """
    Request to write content to a file at the specified path. If the file exists, it will be overwritten with the provided content. If the file doesn't exist, it will be created. This tool will automatically create any directories needed to write the file.
    Parameters:
    - path: (required) The path of the file to write to (relative to the current working directory)
    - content: (required) The content to write to the file. ALWAYS provide the COMPLETE intended content of the file, without any truncation or omissions. You MUST include ALL parts of the file, even if they haven't been modified.
    Usage:
    <write_to_file>
    <path>File path here</path>
    <contents>
    Your file contents here
    </contents>
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

    def __call__(self, path: str, contents: str):
        with open(path, 'w') as file:
            file.write(contents)
        
        return "File written successfully. Updated file content:\n" + contents

class ReadFileTool:
    name = "read_file"
    params = ["path"]
    description = """
    Request to read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file you do not know the contents of, for example to analyze code, review text files, or extract information from configuration files. Automatically extracts raw text from PDF and DOCX files. May not be suitable for other types of binary files, as it returns the raw content as a string.
    Parameters:
    - path: (required) The path of the file to read (relative to the current working directory)
    Usage:
    <read_file>
    <path>File path here</path>
    </read_file>
    """
    examples = """
    Requesting to read a file src/main.py

    <read_file>
    <path>src/main.py</path>
    </read_file>
    """

    def __call__(self, path: str):
        if not os.path.exists(path):
            return f"File at path {path} does not exist"
        with open(path, 'r') as file:
            return "File content:\n" + file.read()

class ReplaceInFileTool:
    name = "replace_in_file"
    params = ["path", "diff"]
    description = """
    Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file. This tool should be used when you need to make targeted changes to specific parts of a file.
    Parameters:
    - path: (required) The path of the file to modify (relative to the current working directory)
    - diff: (required) One or more SEARCH/REPLACE blocks following this exact format:
    ```
    <<<<<<< SEARCH
    [exact content to find]
    =======
    [new content to replace with]
    >>>>>>> REPLACE
    ```
    Critical rules:
    1. SEARCH content must match the associated file section to find EXACTLY:
        * Match character-for-character including whitespace, indentation, line endings
        * Include all comments, docstrings, etc.
    2. SEARCH/REPLACE blocks will ONLY replace the first match occurrence.
        * Including multiple unique SEARCH/REPLACE blocks if you need to make multiple changes.
        * Include *just* enough lines in each SEARCH section to uniquely match each set of lines that need to change.
        * When using multiple SEARCH/REPLACE blocks, list them in the order they appear in the file.
    3. Keep SEARCH/REPLACE blocks concise.
    4. Special operations: To delete code, use empty REPLACE section.
    Usage:
    <replace_in_file>
    <path>File path here</path>
    <diff>
    Search and replace blocks here
    </diff>
    </replace_in_file>
    """
    examples = """
    Requesting to make targeted edits to a file

    <replace_in_file>
    <path>src/components/App.py</path>
    <diff>
    <<<<<<< SEARCH
    import os
    =======
    import subprocess
    >>>>>>> REPLACE

    <<<<<<< SEARCH
    def handleSubmit() {
    saveData();
    setLoading(false);
    }

    =======
    >>>>>>> REPLACE
    </diff>
    </replace_in_file>
    """

    def _parse_diff_blocks(self, diff_str: str) -> list[tuple[str, str]]:
        """
        Parses the diff string into a list of (search_pattern, replacement_text) tuples.
        """
        # Pre-process the diff string to handle escaped newlines and normalize newline conventions:
        # 1. Replace literal "\\n" (escaped newline) with actual newline "\n".
        #    This is important if the diff string comes from a source that escapes them (e.g., JSON, LLM output).
        # 2. Replace literal "\\r" (escaped carriage return) with actual carriage return "\r".
        # 3. Normalize platform-specific newlines (\r\n, \r) to a single \n for consistent regex matching.
        # The order of these replacements can matter.
        
        # Step 1: Handle common escaped characters like \\n, \\r, \\t
        # Note: Be careful with \\ itself if it's meant to be a literal backslash in content.
        # For this tool, \\n and \\r are the most critical for structure.
        processed_diff_str = diff_str.replace('\\\\', '\\') # Handle escaped backslashes first if they might exist e.g. \\\\n -> \\n
        processed_diff_str = processed_diff_str.replace('\\n', '\n')
        processed_diff_str = processed_diff_str.replace('\\r', '\r')
        processed_diff_str = processed_diff_str.replace('\\t', '\t')
        # Add other escaped characters if necessary, e.g. \\" -> "

        # Step 2: Normalize all newline types to \n
        processed_diff_str = processed_diff_str.replace('\r\n', '\n').replace('\r', '\n')

        changes = []
        # Regex to find blocks:
        # ^\s* : Start of line (due to re.MULTILINE), optional leading whitespace.
        # <<<<<<< SEARCH : Delimiter keyword.
        # \s*?\n : Optional trailing whitespace on delimiter line, then a mandatory newline.
        # (.*?) : Captured group for search/replace content (non-greedy, re.DOTALL makes . match newlines).
        # \n^\s*======= : Mandatory newline, then start of next delimiter line.
        # \s*?$ : Optional trailing whitespace on the REPLACE line, then end of line (due to re.MULTILINE).
        pattern = re.compile(
            r"^\s*<<<<<<< SEARCH\s*?\n(.*?)\n^\s*=======\s*?\n(.*?)\n^\s*>>>>>>> REPLACE\s*?$",
            re.DOTALL | re.MULTILINE
        )
        
        for match in pattern.finditer(processed_diff_str):
            search_content = match.group(1)
            replace_content = match.group(2)
            changes.append((search_content, replace_content))
        
        # If no changes were found, it might be useful to log or indicate why.
        # For example, if processed_diff_str is very different from diff_str.
        # However, the calling code already handles the "no changes found" case.

        return changes

    def _apply_changes_to_content(self, original_content: str, changes: list[tuple[str, str]]) -> tuple[str, int]:
        """
        Applies a list of (search, replace) changes to the content.
        Each search pattern is replaced only once per block.
        Returns the modified content and the number of changes successfully applied that resulted in textual difference.
        """
        modified_content = original_content
        applied_count = 0
        
        for search_code, update_code in changes:
            new_content_after_replace = modified_content.replace(search_code, update_code, 1)
            if new_content_after_replace != modified_content:
                applied_count += 1
                modified_content = new_content_after_replace
        return modified_content, applied_count

    def __call__(self, path: str, diff: str) -> str:
        # --- 1. Input Validation ---
        if not path or not isinstance(path, str):
            return f"ERROR: Path parameter is missing or invalid. Path provided: '{str(path)}'."
        if not isinstance(diff, str): # Diff must be a string, even if empty
            return f"ERROR: Diff parameter must be a string. Path: '{path}'."

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
        if not diff.strip():
            return original_content 

        # --- 5. Parse Diff ---
        changes_list: list[tuple[str, str]] = []
        try:
            changes_list = self._parse_diff_blocks(diff)
        except Exception as e: 
            return f"ERROR: Critical error parsing diff blocks for file {path}: {str(e)}"

        if not changes_list: 
            # Provide more context if parsing fails after normalization attempt
            # This can happen if the structure is still not matched after newline processing
            # (e.g. incorrect delimiter keywords, missing =======, etc.)
            return (f"ERROR: No valid SEARCH/REPLACE blocks found in the provided diff for file {path}. "
                    f"File content has not been modified. Ensure diff format is correct and newlines are properly represented. "
                    f"Input diff (first 100 chars): '{diff[:100]}'")
            
        num_changes_requested = len(changes_list)

        # --- 6. Apply Changes ---
        modified_content, applied_count = self._apply_changes_to_content(original_content, changes_list)

        # --- 7. Process Results and Write File if Changed ---
        if applied_count > 0: 
            try:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(modified_content)
                return modified_content
            except Exception as e:
                return f"ERROR: Error writing updated content to file {path}: {str(e)}. In-memory changes were not saved."
        else: 
            return (f"NO_CHANGE_APPLIED: Although {num_changes_requested} change block(s) were provided, "
                    f"no textual changes were made to file '{path}'. "
                    "This could be due to no SEARCH patterns matching, or because all "
                    "REPLACE contents were identical to their corresponding SEARCH contents. "
                    "File content remains unchanged.")