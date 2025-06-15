from .file import WriteToFileTool, ReadFileTool, ReplaceInFileTool
from .shell import ShellTool
from .user import AskUserTool, AttemptCompletionTool
from .browser import BrowserTool

TOOLS_DICT = {
    WriteToFileTool.name: WriteToFileTool,
    ReadFileTool.name: ReadFileTool,
    ReplaceInFileTool.name: ReplaceInFileTool,
    ShellTool.name: ShellTool,
    AskUserTool.name: AskUserTool,
    AttemptCompletionTool.name: AttemptCompletionTool,
    BrowserTool.name: BrowserTool,
}