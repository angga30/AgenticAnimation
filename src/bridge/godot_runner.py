import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class GodotRunner:
    """
    Handles bridging between Python and Godot by copying the base project into a temporary workspace,
    injecting the contract.json, running the Godot process headlessly, and capturing outputs.
    """

    def __init__(self, base_path: str = "godot_base", temp_path: str = "temp_workspace", debug: bool = False):
        self.base_path = Path(base_path)
        self.temp_path = Path(temp_path)
        self.debug = debug
        self.contract_file = self.temp_path / "contract.json"
        self.output_image = self.temp_path / "dailies.png"

    def setup_workspace(self) -> None:
        """Copies the base project to a temporary directory."""
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

        shutil.copytree(self.base_path, self.temp_path)
        print(f"GodotRunner: Workspace created at {self.temp_path}")

    def inject_contract(self, contract_data: Dict[str, Any]) -> None:
        """Writes the JSON data to contract.json in the temp workspace."""
        with open(self.contract_file, "w") as f:
            json.dump(contract_data, f, indent=4)
        print(f"GodotRunner: Contract injected into {self.contract_file}")

    def run_scene(self) -> bool:
        """Runs Godot in headless mode."""
        # Find the godot executable. In a real system, you might want to specify this via ENV var.
        godot_exec = os.environ.get("GODOT_EXECUTABLE", "godot")

        # We assume Godot 4.3 command line syntax
        cmd = [
            godot_exec,
            "--headless",
            "--path", str(self.temp_path.absolute()),
        ]

        print(f"GodotRunner: Executing {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if self.debug:
                print("--- Godot Output ---")
                print(result.stdout)
                if result.stderr:
                    print("--- Godot Errors ---")
                    print(result.stderr)

            if result.returncode != 0:
                print(f"GodotRunner: Godot exited with code {result.returncode}")
                return False

            return True
        except FileNotFoundError:
            print(f"GodotRunner Error: Godot executable '{godot_exec}' not found. Please set GODOT_EXECUTABLE environment variable.")
            return False

    def retrieve_dailies(self, dest_path: str = "latest_dailies.png") -> Optional[str]:
        """Copies the rendered screenshot back to the main directory."""
        if self.output_image.exists():
            shutil.copy(self.output_image, dest_path)
            print(f"GodotRunner: Dailies retrieved to {dest_path}")
            return dest_path
        else:
            print("GodotRunner: No dailies.png found in output.")
            return None

    def cleanup(self) -> None:
        """Removes the temp workspace if not in debug mode."""
        if not self.debug and self.temp_path.exists():
            shutil.rmtree(self.temp_path)
            print(f"GodotRunner: Workspace {self.temp_path} cleaned up.")
        elif self.debug:
            print(f"GodotRunner: Debug mode active. Workspace retained at {self.temp_path}")

    def execute_pipeline(self, contract_data: Dict[str, Any], output_path: str = "latest_dailies.png") -> Optional[str]:
        """Full execution lifecycle."""
        self.setup_workspace()
        self.inject_contract(contract_data)
        success = self.run_scene()
        result_path = None
        if success:
            result_path = self.retrieve_dailies(output_path)
        self.cleanup()
        return result_path

if __name__ == "__main__":
    # Simple test for the runner
    dummy_contract = {
        "camera": {"fov": 50, "position": [0, 2, 5], "target": [0, 1, 0]},
        "lighting": {"ambient": {"color": "#ff0000", "energy": 1.5}},
        "set_design": {
            "structures": [
                {"type": "csg_box", "size": [5, 0.1, 5], "position": [0, 0, 0], "color": "#00ff00"}
            ]
        }
    }
    runner = GodotRunner(debug=True)
    runner.execute_pipeline(dummy_contract)
