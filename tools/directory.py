import os
import glob

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