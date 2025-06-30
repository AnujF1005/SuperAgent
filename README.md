# SuperAgent

SuperAgent is a simple and flexible AI agent framework built with Python that enables autonomous task execution using Large Language Models (LLMs). It provides a structured way to create AI agents that can interact with files, execute shell commands, manage browser interactions, and handle user interactions.

## Features

- 🤖 LLM-powered autonomous agent system
- 🛠️ Modular tool architecture
- 💻 Shell command execution capabilities
- 📂 File system operations
- 🌐 Browser interaction support
- 👤 Interactive user communication
- 📝 Context management for improved agent awareness

## Prerequisites

- Python 3.12+
- OpenAI / Google API key
- Required Python packages (specified in requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SuperAgent.git
cd SuperAgent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the parent directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_api_key_here
```

## Usage

Run the agent with a specific task using the command-line interface:

```bash
python main.py -task "Your task description" -wd /path/to/working/directory
```

Arguments:
- `-task`: The task description for the agent (required)
- `-wd`: Working directory for the agent (optional, defaults to current directory)

## Project Structure

```
SuperAgent/
├── __init__.py
├── agent.py              # Core agent implementation
├── main.py              # CLI entry point
├── prompt.py            # Prompt management
├── response_parser.py   # AI response parsing
├── context_manager/     # Context management system
│   └── context_manager.py
├── tools/               # Available tools
│   ├── browser.py      # Browser interaction tools
│   ├── file.py         # File operation tools
│   ├── shell.py        # Shell command tools
│   ├── terminal_session.py
│   └── user.py         # User interaction tools
└── tests/              # Test suite
```

## Available Tools

1. **File Operations**
   - WriteToFileTool: Write content to files
   - ReadFileTool: Read content from files
   - ReplaceInFileTool: Replace content in existing files

2. **Shell Operations**
   - ShellTool: Execute shell commands
   - TerminalSession: Manage persistent terminal sessions

3. **User Interaction**
   - AskUserTool: Request input from users
   - AttemptCompletionTool: Handle task completion attempts

4. **Browser Operations**
   - BrowserTool: Perform browser-based operations

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgement

- Inspired from Cline (https://github.com/cline/cline)