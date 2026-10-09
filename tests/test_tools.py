import unittest

from veronica_core.tools import execute_tool_call


class ToolArgumentTests(unittest.TestCase):
    def test_non_object_json_arguments_fail_without_raising(self):
        for raw in ("[]", "null", '"prompt"', "1"):
            with self.subTest(raw=raw):
                call = {"id": "c1", "function": {"name": "render_image", "arguments": raw}}
                result = execute_tool_call(call)
                self.assertFalse(result["ok"])
                self.assertIn("JSON object", result["error"])

    def test_object_arguments_succeed(self):
        call = {"id": "c1", "function": {"name": "render_image", "arguments": '{"prompt": "a cat"}'}}
        self.assertTrue(execute_tool_call(call)["ok"])


if __name__ == "__main__":
    unittest.main()
