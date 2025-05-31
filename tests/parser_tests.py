import unittest
from unittest.mock import patch, MagicMock

import sys
import os

# Add the parent directory to the system path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from response_parser import parse_ai_response, ContentType  # Update 'your_module'

class TestParseAIResponse(unittest.TestCase):

    def setUp(self):
        # Mock tool definitions
        self.mock_tools_dict = {
            "TestTool": MagicMock(params=["param1", "param2"]),
            "Echo": MagicMock(params=["msg"]),
        }
        patcher = patch('response_parser.TOOLS_DICT', self.mock_tools_dict)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_plain_text_only(self):
        response = "This is a plain message."
        result = parse_ai_response(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], ContentType.TEXT_CHUNK)
        self.assertEqual(result[0]["text"], "This is a plain message.")

    def test_single_tool_call(self):
        response = "Before<Echo><msg>Hello World</msg></Echo>After"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 3)

        self.assertEqual(result[0]["type"], ContentType.TEXT_CHUNK)
        self.assertEqual(result[0]["text"], "Before")

        self.assertEqual(result[1]["type"], ContentType.TOOL_CALL)
        self.assertEqual(result[1]["tool"], "Echo")
        self.assertEqual(result[1]["params"], {"msg": "Hello World"})

        self.assertEqual(result[2]["type"], ContentType.TEXT_CHUNK)
        self.assertEqual(result[2]["text"], "After")

    def test_tool_call_with_multiple_params(self):
        response = "<TestTool><param1>value1</param1><param2>value2</param2></TestTool>"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 1)
        tool_call = result[0]
        self.assertEqual(tool_call["type"], ContentType.TOOL_CALL)
        self.assertEqual(tool_call["tool"], "TestTool")
        self.assertEqual(tool_call["params"], {
            "param1": "value1",
            "param2": "value2"
        })

    def test_incomplete_tool_param(self):
        response = "<TestTool><param1>value1"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 1)
        tool_call = result[0]
        self.assertEqual(tool_call["type"], ContentType.TOOL_CALL)
        self.assertEqual(tool_call["tool"], "TestTool")
        self.assertEqual(tool_call["params"], {"param1": "value1"})

    def test_malformed_tags(self):
        # Missing closing tag
        response = "<TestTool><param1>incomplete"
        result = parse_ai_response(response)
        self.assertEqual(result[0]["type"], ContentType.TOOL_CALL)
        self.assertEqual(result[0]["params"]["param1"], "incomplete")

    def test_text_before_and_after_tool(self):
        response = "Intro <TestTool><param1>a</param1><param2>b</param2></TestTool> Outro"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["type"], ContentType.TEXT_CHUNK)
        self.assertEqual(result[2]["type"], ContentType.TEXT_CHUNK)
        self.assertIn("Intro", result[0]["text"])
        self.assertIn("Outro", result[2]["text"])

    def test_multiple_tool_calls(self):
        response = "<Echo><msg>Hi</msg></Echo><Echo><msg>Bye</msg></Echo>"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["tool"], "Echo")
        self.assertEqual(result[0]["params"], {"msg": "Hi"})
        self.assertEqual(result[1]["tool"], "Echo")
        self.assertEqual(result[1]["params"], {"msg": "Bye"})
    
    def test_tool_call_no_params(self):
        self.mock_tools_dict["NoParamTool"] = MagicMock(params=[])
        response = "<NoParamTool></NoParamTool>"
        with patch('response_parser.TOOLS_DICT', self.mock_tools_dict):
            result = parse_ai_response(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool"], "NoParamTool")
        self.assertEqual(result[0]["params"], {})

    def test_mixed_text_and_multiple_tools(self):
        response = "Start<Echo><msg>Hi</msg></Echo>Middle<TestTool><param1>One</param1><param2>Two</param2></TestTool>End"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["text"], "Start")
        self.assertEqual(result[1]["tool"], "Echo")
        self.assertEqual(result[2]["text"], "Middle")
        self.assertEqual(result[3]["tool"], "TestTool")
        self.assertEqual(result[4]["text"], "End")
    
    def test_param_with_tag_like_content(self):
        response = "<Echo><msg>Text with < and > symbols</msg></Echo>"
        result = parse_ai_response(response)
        self.assertEqual(result[0]["tool"], "Echo")
        self.assertEqual(result[0]["params"]["msg"], "Text with < and > symbols")

    def test_incomplete_tool_no_params(self):
        response = "<TestTool>"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], ContentType.TOOL_CALL)
        self.assertEqual(result[0]["tool"], "TestTool")
        self.assertEqual(result[0]["params"], {})

    def test_nested_tool_calls(self):
        response = "<TestTool><param1><Echo><msg>Hello</msg></Echo></param1></TestTool>"
        result = parse_ai_response(response)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], ContentType.TOOL_CALL)
        self.assertEqual(result[0]["tool"], "TestTool")
        self.assertEqual(result[0]["params"]["param1"], "<Echo><msg>Hello</msg></Echo>")

if __name__ == "__main__":
    unittest.main()
