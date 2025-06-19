from tools import TOOLS_DICT
from enum import Enum

class ContentType(Enum):
    TOOL_CALL = 1
    TEXT_CHUNK = 2

def parse_ai_response(response: str):
    tool_names = list(TOOLS_DICT.keys())
    tool_start_tags = {f"<{tool_name}>": tool_name for tool_name in tool_names}
    
    accumulator: str = ""
    current_tool: str = None
    current_tool_required_params = {}
    param_start_index: int = -1
    current_param: str = None
    all_params: dict = {}

    content_blocks = []

    for ind, char in enumerate(response):
        accumulator += char

        if current_tool is None:
            for start_tag, tool_name in tool_start_tags.items():
                if accumulator.endswith(start_tag):
                    if len(accumulator) > len(start_tag):
                        content_blocks.append({
                            "type": ContentType.TEXT_CHUNK,
                            "content": accumulator[:-len(start_tag)],
                        })
                        accumulator = ""
                    current_tool = tool_name
                    current_tool_required_params = {f"<{param}>": param for param in TOOLS_DICT[tool_name].params["required"] + TOOLS_DICT[tool_name].params["optional"]}
                    break
        else:
            if (current_param != None) and (accumulator.endswith(f"</{current_param}>")):
                length_of_ending_tag = len(f"</{current_param}>")
                param_value = accumulator[param_start_index:-length_of_ending_tag]
                all_params[current_param] = param_value
                param_start_index = -1
                current_param = None
            else:
                for param in current_tool_required_params.keys():
                    if accumulator.endswith(param):
                        param_start_index = len(accumulator)
                        current_param = current_tool_required_params[param]
                        break
                
            if accumulator.endswith(f"</{current_tool}>"):
                content_blocks.append({
                    "type": ContentType.TOOL_CALL,
                    "tool": current_tool,
                    "params": all_params,
                })

                current_tool: str = None
                current_tool_required_params = {}
                param_start_index: int = -1
                current_param: str = None
                all_params = {}

                accumulator = ""
    
    if len(accumulator) > 0 and current_tool is not None:
        # Incomplete tool call in Agent reponse

        if current_param != None:
            param_value = accumulator[param_start_index:]
            all_params[current_param] = param_value
        
        content_blocks.append({
            "type": ContentType.TOOL_CALL,
            "tool": current_tool,
            "params": all_params,
        })
    elif len(accumulator) > 0:
        content_blocks.append({
            "type": ContentType.TEXT_CHUNK,
            "content": accumulator,
        })

    return content_blocks
    