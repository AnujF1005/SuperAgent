import os
import re

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
        "optional": []
    }
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
            return f"Content of file {path}:\n" + file.read()

class ReplaceInFileTool:
    name = "replace_in_file"
    params = {
        "required": ["path", "diff"],
        "optional": []
    }
    description = """
    Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file. This tool should be used when you need to make targeted changes to specific parts of a file.
    Parameters:
    - path: (required) The path of the file to modify (relative to the current working directory)
    - diff: (required) One or more SEARCH and REPLACE blocks following this exact format:
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
    2. SEARCH - REPLACE blocks will ONLY replace the first match occurrence.
        * Including multiple unique SEARCH/REPLACE blocks if you need to make multiple changes.
        * Include *just* enough lines in each SEARCH section to uniquely match each set of lines that need to change.
        * When using multiple SEARCH/REPLACE blocks, list them in the order they appear in the file.
    3. Keep SEARCH - REPLACE blocks concise.
    4. Every SEARCH block must have a corresponding REPLACE block.
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
        This version is robust against missing final '>>>>>>> REPLACE' delimiters.
        """
        # Normalize all newline types to \n for consistent processing
        processed_diff_str = diff_str.replace('\r\n', '\n').replace('\r', '\n')
        
        # A block is defined as starting with <<<<<<< SEARCH. We split the diff by this
        # delimiter, using a lookahead `(?=...)` to keep the delimiter with its content.
        chunks = re.split(r'(^\s*<<<<<<< SEARCH)', processed_diff_str, flags=re.MULTILINE)
        
        changes = []
        
        # The split results in `['preamble', 'delim1', 'content1', 'delim2', 'content2', ...]`.
        # We iterate through the (delimiter, content) pairs.
        i = 1
        while i < len(chunks):
            # Check for a delimiter followed by its content block.
            if i + 1 >= len(chunks):
                break

            block_content = chunks[i] + chunks[i+1]
            
            # Define the separator pattern between SEARCH and REPLACE blocks.
            separator_pattern = r'\n^\s*=======\s*\n'
            
            # A valid block must contain the separator. If not found, skip this chunk.
            if not re.search(separator_pattern, block_content, flags=re.MULTILINE | re.DOTALL):
                i += 2
                continue

            # Split the block into the part before and after the separator.
            header_and_search, replace_and_trailer = re.split(
                separator_pattern, block_content, maxsplit=1, flags=re.MULTILINE | re.DOTALL
            )
            
            # Extract search content by removing the '<<<<<<< SEARCH' header.
            search_content = re.sub(r'^\s*<<<<<<< SEARCH\s*\n', '', header_and_search, flags=re.MULTILINE)
            
            # The replace content is the second part. We clean it by removing the optional
            # '>>>>>>> REPLACE' trailer and any trailing whitespace.
            # The `\s*$` ensures we match the trailer even if it has trailing spaces or newlines.
            replace_content = re.sub(r'\n\s*>>>>>>> REPLACE\s*$', '', replace_and_trailer).rstrip()

            changes.append((search_content, replace_content))
            i += 2 # Move to the next delimiter-content pair
            
        return changes

    def _line_trimmed_fallback_match(self, original_content: str, search_content: str, start_index: int) -> tuple[int, int] | None:
        """
        Attempts a line-trimmed fallback match for the given search content in the original content.
        It tries to match `search_content` lines against a block of lines in `original_content` starting
        from `start_index`. Lines are matched by trimming leading/trailing whitespace and ensuring
        they are identical afterwards.
        Returns [matchIndexStart, matchIndexEnd] if found, or None if not found.
        """
        original_lines = original_content.split("\n")
        search_lines = search_content.split("\n")

        # Trim trailing empty line if exists (from the trailing \n in search_content)
        if search_lines and search_lines[-1] == "":
            search_lines.pop()

        if not search_lines: # Handle empty search content for line-trimmed match
            return None

        # Find the line number where start_index falls
        start_line_num = 0
        current_char_index = 0
        while current_char_index < start_index and start_line_num < len(original_lines):
            current_char_index += len(original_lines[start_line_num]) + 1 # +1 for \n
            start_line_num += 1

        # For each possible starting position in original content
        for i in range(start_line_num, len(original_lines) - len(search_lines) + 1):
            matches = True
            # Try to match all search lines from this position
            for j in range(len(search_lines)):
                original_trimmed = original_lines[i + j].strip()
                search_trimmed = search_lines[j].strip()

                if original_trimmed != search_trimmed:
                    matches = False
                    break
            
            # If we found a match, calculate the exact character positions
            if matches:
                # Find start character index
                match_start_index = 0
                for k in range(i):
                    match_start_index += len(original_lines[k]) + 1 # +1 for \n

                # Find end character index
                match_end_index = match_start_index
                for k in range(len(search_lines)):
                    match_end_index += len(original_lines[i + k]) + 1 # +1 for \n
                
                # Adjust match_end_index if the last line of original_content doesn't end with a newline
                # This is important for accurate slicing
                if i + len(search_lines) == len(original_lines) and not original_content.endswith('\n'):
                    match_end_index -= 1 # Remove the extra +1 for the non-existent newline

                return [match_start_index, match_end_index]
        return None

    def _block_anchor_fallback_match(self, original_content: str, search_content: str, start_index: int) -> tuple[int, int] | None:
        """
        Attempts to match blocks of code by using the first and last lines as anchors.
        This is a third-tier fallback strategy that helps match blocks where we can identify
        the correct location by matching the beginning and end, even if the exact content
        differs slightly.
        """
        original_lines = original_content.split("\n")
        search_lines = search_content.split("\n")

        # Only use this approach for blocks of 3+ lines
        if len(search_lines) < 3:
            return None

        # Trim trailing empty line if exists
        if search_lines and search_lines[-1] == "":
            search_lines.pop()
        
        if not search_lines: # Handle empty search content after pop
            return None

        first_line_search = search_lines[0].strip()
        last_line_search = search_lines[-1].strip()
        search_block_size = len(search_lines)

        # Find the line number where start_index falls
        start_line_num = 0
        current_char_index = 0
        while current_char_index < start_index and start_line_num < len(original_lines):
            current_char_index += len(original_lines[start_line_num]) + 1
            start_line_num += 1

        # Look for matching start and end anchors
        for i in range(start_line_num, len(original_lines) - search_block_size + 1):
            # Check if first line matches
            if original_lines[i].strip() != first_line_search:
                continue

            # Check if last line matches at the expected position
            if original_lines[i + search_block_size - 1].strip() != last_line_search:
                continue

            # Calculate exact character positions
            match_start_index = 0
            for k in range(i):
                match_start_index += len(original_lines[k]) + 1

            match_end_index = match_start_index
            for k in range(search_block_size):
                match_end_index += len(original_lines[i + k]) + 1
            
            # Adjust match_end_index if the last line of original_content doesn't end with a newline
            if i + search_block_size == len(original_lines) and not original_content.endswith('\n'):
                match_end_index -= 1

            return [match_start_index, match_end_index]
        return None

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
            return (f"ERROR: No valid SEARCH/REPLACE blocks found in the provided diff for file {path}. "
                    f"File content has not been modified. Ensure diff format is correct and newlines are properly represented. "
                    f"Input diff (first 100 chars): '{diff[:100]}'")
            
        num_changes_requested = len(changes_list)
        modified_content = original_content
        applied_count = 0
        last_processed_index = 0 # Keep track of the last processed character index in the original content

        # --- 6. Apply Changes ---
        for search_code, update_code in changes_list:
            match_start_index = -1
            match_end_index = -1

            # Attempt 1: Exact match
            exact_index = modified_content.find(search_code, last_processed_index)
            if exact_index != -1:
                match_start_index = exact_index
                match_end_index = exact_index + len(search_code)
            else:
                # Attempt 2: Line-trimmed fallback match
                line_match = self._line_trimmed_fallback_match(modified_content, search_code, last_processed_index)
                if line_match:
                    match_start_index, match_end_index = line_match
                else:
                    # Attempt 3: Block anchor fallback match
                    block_match = self._block_anchor_fallback_match(modified_content, search_code, last_processed_index)
                    if block_match:
                        match_start_index, match_end_index = block_match
            
            if match_start_index != -1:
                # Reconstruct the content with the replacement
                modified_content = (
                    modified_content[:match_start_index] +
                    update_code +
                    modified_content[match_end_index:]
                )
                applied_count += 1
                # Update last_processed_index for the next search
                # This is crucial for sequential replacements
                last_processed_index = match_start_index + len(update_code)
            else:
                # If no match found for a block, it's an error or warning
                # For now, we'll just report it and continue, but a more robust system might stop or ask for clarification.
                print(f"WARNING: SEARCH block did not find a match in file {path} starting from index {last_processed_index}. Search content (first 100 chars): '{search_code[:100]}'")

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