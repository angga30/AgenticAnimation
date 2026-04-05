import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

class GodotRunner:
    """
    Handles bridging between Python and Godot by copying the base project into a temporary workspace,
    injecting the contract.json, running the Godot process headlessly, and capturing outputs.
    """

    def __init__(self, base_path: Optional[str] = None, debug: bool = False):
        # Resolve base_path relative to module path if not explicitly provided
        if base_path:
            self.base_path = Path(base_path).resolve()
        else:
            # Fallback to godot_base in project root relative to this module
            self.base_path = (Path(__file__).parent.parent.parent / "godot_base").resolve()

        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir_obj.name)
        self.debug = debug
        self.contract_file = self.temp_path / "contract.json"
        self.output_image = self.temp_path / "dailies.png"
        self.output_video = self.temp_path / "final_render.avi" # Godot natively exports to AVI unless further configured
        self.output_video_mp4 = self.temp_path / "final_render.mp4"

        # Create .debug folder in project root for saving contracts
        self.debug_dir = Path(__file__).parent.parent.parent / ".debug"
        self.debug_dir.mkdir(exist_ok=True)

    def setup_workspace(self) -> None:
        """Copies the base project to a temporary directory."""
        shutil.copytree(self.base_path, self.temp_path, dirs_exist_ok=True)
        print(f"GodotRunner: Workspace created at {self.temp_path}")

    def inject_contract(self, contract_data: Dict[str, Any]) -> None:
        """Writes the JSON data to contract.json in the temp workspace and .debug folder."""
        with open(self.contract_file, "w") as f:
            json.dump(contract_data, f, indent=4)
        print(f"GodotRunner: Contract injected into {self.contract_file}")

        # Save contract to .debug folder for debugging
        import time
        timestamp = int(time.time())
        debug_contract_path = self.debug_dir / f"contract_{timestamp}.json"
        with open(debug_contract_path, "w") as f:
            json.dump(contract_data, f, indent=4)
        print(f"GodotRunner: Contract saved to debug folder: {debug_contract_path}")

    def run_scene(self, dump_frame: bool = True, duration: float = 2.0) -> bool:
        """Runs Godot in headless mode.
        If dump_frame is True, captures a single screenshot.
        If dump_frame is False, exports a video via --write-movie.
        """
        godot_exec = os.environ.get("GODOT_EXECUTABLE", "godot")

        # In debug mode, we omit --headless so the user can see the rendering happen in real-time
        headless_args = ["--headless"] if not self.debug else []

        if dump_frame:
            cmd = [godot_exec] + headless_args + [
                "--path", str(self.temp_path.absolute()),
                "--",
                "--dump-frame", str(self.output_image.absolute())
            ]
        else:
            fps = 30
            cmd = [godot_exec] + headless_args + [
                "--path", str(self.temp_path.absolute()),
                "--write-movie", str(self.output_video.absolute()),
                "--fixed-fps", str(fps),
                "--",
                "--render-video",
                "--duration", str(duration)
            ]

        # Add a fallback for linux headless rendering if pure headless fails in some environments
        if sys.platform == "linux" and os.environ.get("USE_XVFB", "0") == "1" and not self.debug:
            cmd = ["xvfb-run", "--auto-servernum"] + cmd

        print(f"GodotRunner: Executing {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
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
        except subprocess.TimeoutExpired:
            print(f"GodotRunner Error: Execution of '{godot_exec}' timed out after 300 seconds.")
            return False

    def retrieve_dailies(self, dest_path: str = "latest_dailies.png") -> Optional[str]:
        """Copies the rendered screenshot back to the main directory."""
        if self.output_image.exists():
            shutil.copy(self.output_image, dest_path)
            print(f"GodotRunner: Dailies retrieved to {dest_path}")
            return dest_path
        else:
            print("GodotRunner: No dailies found in output.")
            return None

    def convert_to_mp4(self) -> bool:
        """Converts the output AVI to MP4 using FFmpeg."""
        if not self.output_video.exists():
            return False

        cmd = [
            "ffmpeg", "-y",
            "-i", str(self.output_video.absolute()),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            str(self.output_video_mp4.absolute())
        ]

        print(f"GodotRunner: Converting to MP4 via FFmpeg...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and self.output_video_mp4.exists():
                return True
            else:
                print(f"GodotRunner: FFmpeg failed: {result.stderr}")
                return False
        except FileNotFoundError:
            print("GodotRunner: FFmpeg not found on system. Returning raw AVI instead.")
            return False

    def retrieve_video(self, dest_path: str = "latest_render.mp4") -> Optional[str]:
        """Copies the rendered video back to the main directory. Returns MP4 if possible, else AVI."""
        if self.convert_to_mp4():
            if dest_path.endswith(".avi"):
                dest_path = dest_path.replace(".avi", ".mp4")
            shutil.copy(self.output_video_mp4, dest_path)
            print(f"GodotRunner: MP4 Video retrieved to {dest_path}")
            return dest_path
        elif self.output_video.exists():
            if dest_path.endswith(".mp4"):
                dest_path = dest_path.replace(".mp4", ".avi")
            shutil.copy(self.output_video, dest_path)
            print(f"GodotRunner: AVI Video retrieved to {dest_path} (FFmpeg conversion failed/skipped)")
            return dest_path
        else:
            print("GodotRunner: No video found in output.")
            return None

    def cleanup(self) -> None:
        """Removes the temp workspace if not in debug mode."""
        if not self.debug:
            self.temp_dir_obj.cleanup()
            print(f"GodotRunner: Workspace {self.temp_path} cleaned up.")
        elif self.debug:
            print(f"GodotRunner: Debug mode active. Workspace retained at {self.temp_path}")

    def execute_pipeline(self, contract_data: Dict[str, Any], output_path: str = "latest_dailies.png", mode: str = "frame", duration: float = 2.0) -> Optional[str]:
        """Full execution lifecycle. mode can be 'frame' or 'video'."""
        result_path = None
        try:
            self.setup_workspace()
            self.inject_contract(contract_data)

            if mode == "video":
                success = self.run_scene(dump_frame=False, duration=duration)
                if success:
                    result_path = self.retrieve_video(output_path)
            else:
                success = self.run_scene(dump_frame=True, duration=duration)
                if success:
                    result_path = self.retrieve_dailies(output_path)
        finally:
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
