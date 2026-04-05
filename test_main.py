import unittest
from src.core.state import ProductionState
from src.bridge.godot_runner import GodotRunner

class TestBasicImports(unittest.TestCase):
    def test_imports(self):
        import src.main
        self.assertIsNotNone(src.main.build_production_graph)

        import src.agents
        self.assertIsNotNone(src.agents.director_node)

        import src.core.llm_factory
        self.assertIsNotNone(src.core.llm_factory.get_llm)

        import src.core.image_factory
        self.assertIsNotNone(src.core.image_factory.generate_image_bytes)

    def test_state_creation(self):
        state = ProductionState(user_prompt="Hello world", retake_count=0)
        self.assertEqual(state["user_prompt"], "Hello world")
        self.assertEqual(state["retake_count"], 0)

if __name__ == "__main__":
    unittest.main()
