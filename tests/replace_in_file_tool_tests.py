import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import sys
import tempfile

# Add the parent directory to the system path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from tools import ReplaceInFileTool

class TestReplaceInFileTool(unittest.TestCase):
    def setUp(self):
        self.tool = ReplaceInFileTool()
        self.valid_path = "test_file.py"
        self.original_content = "import os\nprint('Hello')\n"
        self.diff = (
            "<<<<<<< SEARCH\n"
            "import os\n"
            "=======\n"
            "import sys\n"
            ">>>>>>> REPLACE"
        )

    @patch("builtins.open", new_callable=mock_open, read_data="import os\nprint('Hello')\n")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_basic_replacement(self, mock_isfile, mock_exists, mock_file):
        result = self.tool(self.valid_path, self.diff)
        self.assertIn("import sys", result)
        mock_file.assert_called_with(self.valid_path, 'w', encoding='utf-8')

    @patch("builtins.open", new_callable=mock_open, read_data="import os\nprint('Hello')\n")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_no_change_applied(self, mock_isfile, mock_exists, mock_file):
        # SEARCH does not match
        bad_diff = (
            "<<<<<<< SEARCH\n"
            "import foo\n"
            "=======\n"
            "import sys\n"
            ">>>>>>> REPLACE"
        )
        result = self.tool(self.valid_path, bad_diff)
        self.assertTrue(result.startswith("NO_CHANGE_APPLIED"))

    @patch("os.path.exists", return_value=False)
    def test_file_not_found(self, mock_exists):
        result = self.tool("missing.py", self.diff)
        self.assertTrue(result.startswith("ERROR: File not found"))

    @patch("os.path.exists", return_value=True)
    @patch("os.path.isfile", return_value=False)
    def test_path_is_not_file(self, mock_isfile, mock_exists):
        result = self.tool("folder/", self.diff)
        self.assertTrue(result.startswith("ERROR: Path is not a file"))

    @patch("builtins.open", side_effect=Exception("Read failed"))
    @patch("os.path.exists", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_read_error(self, mock_isfile, mock_exists, mock_open_fn):
        result = self.tool(self.valid_path, self.diff)
        self.assertTrue(result.startswith("ERROR: Error reading file"))

    def test_invalid_diff_format(self):
        invalid_diff = "no proper markers"
        with patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", mock_open(read_data=self.original_content)):
            result = self.tool(self.valid_path, invalid_diff)
            self.assertTrue(result.startswith("ERROR: No valid SEARCH/REPLACE"))

    def test_empty_diff(self):
        with patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", mock_open(read_data=self.original_content)):
            result = self.tool(self.valid_path, "   \n")
            self.assertEqual(result, self.original_content)

    def test_non_string_diff(self):
        result = self.tool(self.valid_path, diff=1234)
        self.assertTrue(result.startswith("ERROR: Diff parameter must be a string"))

    def test_invalid_path_type(self):
        result = self.tool(None, diff=self.diff)
        self.assertTrue(result.startswith("ERROR: Path parameter is missing or invalid."))

    @patch("builtins.open", new_callable=mock_open, read_data="import os\nprint('Hello')\n")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_multiple_blocks_applied(self, mock_isfile, mock_exists, mock_file):
        original = "import os\nprint('Hello')\ndef func():\n    pass\n"
        multi_diff = (
            "<<<<<<< SEARCH\n"
            "import os\n"
            "=======\n"
            "import sys\n"
            ">>>>>>> REPLACE\n"
            "<<<<<<< SEARCH\n"
            "def func():\n    pass\n"
            "=======\n"
            "def func():\n    print('done')\n"
            ">>>>>>> REPLACE"
        )
        mock_file().read.return_value = original
        result = self.tool(self.valid_path, multi_diff)
        self.assertIn("import sys", result)
        self.assertIn("print('done')", result)

class TestReplaceInFileToolIntegration(unittest.TestCase):

    def setUp(self):
        self.tool = ReplaceInFileTool()

    def test_file_content_updated_correctly(self):
        original = "import os\nprint('Hello')\n"
        diff = (
            "<<<<<<< SEARCH\n"
            "import os\n"
            "=======\n"
            "import sys\n"
            ">>>>>>> REPLACE"
        )

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(original)
            tmp_path = tmp.name

        try:
            # Run tool
            result = self.tool(path=tmp_path, diff=diff)

            # Read file after tool runs
            with open(tmp_path, "r", encoding="utf-8") as f:
                updated = f.read()

            self.assertIn("import sys", updated)
            self.assertNotIn("import os", updated)
            self.assertEqual(result, updated)

        finally:
            os.remove(tmp_path)

    def test_file_content_updated_with_multiple_blocks(self):
        original = "import os\nprint('Hello')\ndef func():\n    pass\n"
        diff = (
            "<<<<<<< SEARCH\n"
            "import os\n"
            "=======\n"
            "import sys\n"
            ">>>>>>> REPLACE\n"
            "<<<<<<< SEARCH\n"
            "def func():\n    pass\n"
            "=======\n"
            "def func():\n    print('done')\n"
            ">>>>>>> REPLACE"
        )

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(original)
            tmp_path = tmp.name

        try:
            result = self.tool(tmp_path, diff)

            with open(tmp_path, "r", encoding="utf-8") as f:
                updated = f.read()

            self.assertIn("import sys", updated)
            self.assertIn("print('done')", updated)
            self.assertNotIn("import os", updated)
            self.assertNotIn("pass", updated)
            self.assertEqual(result, updated)
        finally:
            os.remove(tmp_path)

    def test_delete_code_block(self):
        original = "def cleanup():\n    os.remove('temp')\n"
        diff = (
            "<<<<<<< SEARCH\n"
            "def cleanup():\n    os.remove('temp')\n"
            "=======\n"
            "\n"
            ">>>>>>> REPLACE"
        )

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(original)
            tmp_path = tmp.name

        try:
            result = self.tool(tmp_path, diff)

            with open(tmp_path, "r", encoding="utf-8") as f:
                updated = f.read()

            self.assertEqual(updated.strip(), "")  # File should be empty
            self.assertEqual(result.strip(), "")
        finally:
            os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
