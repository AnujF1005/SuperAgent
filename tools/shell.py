
class ShellTool:
    name = "shell"
    params = ["command", "requires_approval"]
    description = """
    Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does. For command chaining, use the appropriate chaining syntax for the user's shell. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Commands will be executed in the current working directory.
    Parameters:
    - command: (required) The CLI command to execute. This should be valid for the current operating system. Ensure the command is properly formatted and does not contain any harmful instructions.
    - requires_approval: (required) A boolean indicating whether this command requires explicit user approval before execution in case the user has auto-approve mode enabled. Set to 'true' for potentially impactful operations like installing/uninstalling packages, deleting/overwriting files, system configuration changes, network operations, or any commands that could have unintended side effects. Set to 'false' for safe operations like reading files/directories, running development servers, building projects, and other non-destructive operations.
    Usage:
    <shell>
    <command>Your command here</command>
    <requires_approval>true or false</requires_approval>
    </shell>
    """
    examples = """
    Requesting to execute a command

    <shell>
    <command>conda create -n AIENV python=3.11</command>
    <requires_approval>true</requires_approval>
    </shell>

    <shell>
    <command>ls -ld *</command>
    <requires_approval>false</requires_approval>
    </shell>
    """

    # terminal_session must be injected by the Agent at call time!
    def __call__(self, command: str, requires_approval: str, terminal_session=None):
        if requires_approval.lower() == "true":
            ip = input(f"Approval required (y/n) for executing following command:\n{command}\n>> ")
            if ip.lower() == "n":
                return f"User denied request to exeute command: {command}"
        if terminal_session is None:
            return "[SuperAgent] ERROR: No terminal_session provided to ShellTool (this is a coding bug)."

        output = terminal_session.send_command_and_capture(command)
        return f"Stdout/Stderr:\n{output}"
