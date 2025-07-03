import os
import glob
import re

class LSTool:
    name = "list_directory"
    params = {
        "required": ["path"],
        "optional": []
    }
    description = """
    Lists the names of files and subdirectories directly within a specified directory path.
    Parameters:
    - path: (required) The path of the directory to list (relative to the current working directory)
    Usage:
    <list_directory>
    <path>Directory path here</path>
    </list_directory>
    """
    examples = """
    <list_directory>
    <path>src</path>
    </list_directory>
    """

    def __call__(self, path: str):
        # Ensure directory exists
        if not os.path.exists(path):
            return f"Directory at path {path} does not exist"
        
        if not os.path.isdir(path):
            return f"Path {path} is not a directory"
        
        result = ""
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                result += f"{item} (File)\n"
            elif os.path.isdir(full_path):
                result += f"{item} (Directory)\n"
            else:
                result += f"{item} (Unknown)\n"
        if result == "":
            result = f"Directory at {path} is empty."
        return result


class GlobTool:
    name = "glob_directory"
    params = {
        "required": ["path", "pattern"],
        "optional": []
    }
    description = """
    Efficiently finds files matching specific glob patterns (e.g., `src/**/*.ts`, `**/*.md`), returning relative paths.
    Ideal for quickly locating files based on their name or path structure, especially in large codebases.
    Parameters:
    - path: (required) The path of the directory to search within (relative to the current working directory)
    - pattern: (required) The glob pattern to match files against (e.g., '**/*.py', 'docs/*.md').
    Usage:
    <glob_directory>
    <path>Directory path here</path>
    <pattern>Glob pattern here</pattern>
    </glob_directory>
    """
    examples = """
    <glob_directory>
    <path>src</path>
    <pattern>**/*.py</pattern>
    </glob_directory>
    """

    def __call__(self, path: str, pattern: str):
        # Ensure directory exists
        if not os.path.exists(path):
            return f"Directory at path {path} does not exist"
        
        if not os.path.isdir(path):
            return f"Path {path} is not a directory"
        
        glob_result = glob.glob(pattern, root_dir=path)

        if len(glob_result) == 0:
            return f"No file found matching pattern {pattern} at path {path}"
        
        result = ""
        for item in glob_result:
            result += f"{os.path.join(path, item)}\n"

        return result


class GrepTool:
    name = "grep_search_text"
    params = {
        "required": ["path", "pattern"],
        "optional": ["include"]
    }
    description = """
    Searches for a regular expression pattern within the content of files in a specified directory.
    Can filter files by a glob pattern. Returns the lines containing matches, along with their file paths and line numbers.
    Parameters:
    - path: (required) The path of the directory to search within (relative to the current working directory)
    - pattern: (required) The regular expression (regex) pattern to search for within file contents (e.g., 'function\\s+myFunction', 'import\\s+\\{.*\\}\\s+from\\s+.*').
    - include: (optional) A glob pattern to filter which files are searched (e.g., '*.js', '*.{ts,tsx}', 'src/**'). If omitted, searches all files.
    Usage:
    <grep_search_text>
    <path>Directory path here</path>
    <pattern>Regular expression pattern here</pattern>
    <include>Glob pattern here</include>
    </grep_search_text>
    """
    examples = """
    <grep_search_text>
    <path>src</path>
    <pattern>import\\s+\\{.*\\}\\s+from\\s+.*</pattern>
    </grep_search_text>

    <grep_search_text>
    <path>src</path>
    <pattern>import\\s+\\{.*\\}\\s+from\\s+.*</pattern>
    <include>**/*.py</include>
    </grep_search_text>
    """

    def __call__(self, path: str, pattern: str, include: str = None):
        # TODO: Ignore global ignore patterns e.g. .gitignore. Also use robust methods such as used by Gemini CLI.
        # Ensure directory exists
        if not os.path.exists(path):
            return f"Error: Directory at path '{path}' does not exist."
        
        if not os.path.isdir(path):
            return f"Error: Path '{path}' is not a directory."

        # If include is not provided, search all files recursively
        if include is None:
            include = '**/*'

        # Find all paths matching the pattern. `recursive=True` is needed for `**`
        try:
            files_to_search = glob.glob(include, recursive=True, root_dir=path)
        except Exception as e:
            return f"Error with include glob pattern '{include}': {e}"

        results = []
        try:
            # Compile the regex for efficiency and to validate it
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            return f"Error: Invalid regular expression: {e}"

        for file_path in files_to_search:
            # The glob might match directories, so we check if it's a file
            if os.path.isfile(file_path):
                try:
                    # Open file, ignoring errors for binary files that can't be decoded
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_number, line in enumerate(f, 1):
                            if compiled_pattern.search(line):
                                # Format: path:line_number:content
                                results.append(f"File: {file_path}\nLine number: {line_number}\nLine: {line.strip()}\n\n")
                except (IOError, OSError) as e:
                    results.append(f"Error reading file '{file_path}': {e}\n\n")

        if not results:
            return "No matches found."
        
        return "\n".join(results)
        