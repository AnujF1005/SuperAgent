import os

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
        
        return contents

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
            return file.read()

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
    3. Keep SEARCH/REPLACE blocks concise:
        * Break large SEARCH/REPLACE blocks into a series of smaller blocks that each change a small portion of the file.
        * Include just the changing lines, and a few surrounding lines if needed for uniqueness.
        * Do not include long runs of unchanging lines in SEARCH/REPLACE blocks.
        * Each line must be complete. Never truncate lines mid-way through as this can cause matching failures.
    4. Special operations:
        * To move code: Use two SEARCH/REPLACE blocks (one to delete from original + one to insert at new location)
        * To delete code: Use empty REPLACE section
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

    <<<<<<< SEARCH
    return None
    =======
    def handleSubmit() {
    saveData();
    setLoading(false);
    }

    return handleSubmit()
    >>>>>>> REPLACE
    </diff>
    </replace_in_file>
    """
    
    def __parse_updates(self, updates: str):
        lines = updates.split('\n')

        changes = [] # List of tuple of search string and code to update.

        current_status = "none"
        search_code = ""
        update_code = ""

        for line in lines:
            if "<<<<<<< SEARCH" in line.strip():
                current_status = "search"
                search_code = ""
                continue
            elif "=======" == line.strip():
                current_status = "update"
                update_code = ""
                continue
            elif ">>>>>>> REPLACE" in line.strip():
                current_status = "none"
                changes.append((search_code, update_code))
                continue
            
            if current_status == "search":
                search_code += line
            elif current_status == "update":
                update_code += line
            
        return changes

    def __update_file(self, path: str, diff: str):
        if not os.path.exists(path):
            return f"File at path {path} does not exist"
        
        changes = self.__parse_updates(diff)
        
        with open(path, 'r') as file:
            content = file.read()

        print(changes)

        for search_code, update_code in changes:
            content = content.replace(search_code, update_code)
        
        with open(path, 'w') as file:
            file.write(content)
        
        return content
    
    def __call__(self, path: str, updates: str):
        return self.__update_file(path, updates)