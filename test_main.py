import unittest
from src.core.state import ProductionState
from src.bridge.godot_runner import GodotRunner

class TestBasicImports(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(True)

    def test_state_creation(self):
        state = ProductionState(user_prompt="Hello world", retake_count=0)
        self.assertEqual(state["user_prompt"], "Hello world")
        self.assertEqual(state["retake_count"], 0)

if __name__ == "__main__":
    unittest.main()
