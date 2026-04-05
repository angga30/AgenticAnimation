import os
from io import BytesIO
from PIL import Image
from rembg import remove
from src.core.state import ProductionState
from src.core.image_factory import generate_image_bytes

def process_and_save_image(img_bytes: bytes, output_path: str, remove_bg: bool = False) -> str:
    """Processes the raw image bytes (removes bg if needed, resizes) and saves to path."""
    if remove_bg:
        img_bytes = remove(img_bytes)

    img = Image.open(BytesIO(img_bytes))

    # Resize down characters/props to save memory in Godot
    if remove_bg:
        img = img.resize((512, 512))
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    img.save(output_path)
    return output_path

def asset_generator_node(state: ProductionState) -> ProductionState:
    """Reads scenario and generates assets (background, characters, props)."""
    print("🎨 Asset Generator: Creating assets via agnostic Image Factory & Rembg...")

    assets_dir = os.path.abspath("generated_assets")
    os.makedirs(assets_dir, exist_ok=True)

    generated_assets = state.get("generated_assets", {})
    scenario = state.get("scenario", {})

    # Define generation queue: tuple of (asset_id, prompt, is_bg)
    queue = []

    # 1. Background
    bg_desc = scenario.get("background_desc")
    if bg_desc:
        queue.append(("background_01", f"A video game background, matte painting style, empty set without characters. {bg_desc}", True))

    # 2. Characters
    for char in scenario.get("characters", []):
        char_id = char.get("id", "char_01")
        desc = char.get("description", "A standard character")
        queue.append((char_id, f"A 2D sprite of a character on a solid white background, full body, standing straight. {desc}", False))

    # 3. Props
    for prop in scenario.get("props", []):
        prop_id = prop.get("id", "prop_01")
        desc = prop.get("description", "A simple prop")
        queue.append((prop_id, f"A 2D sprite of an object on a solid white background. {desc}", False))

    for asset_id, prompt, is_bg in queue:
        if asset_id in generated_assets:
            continue

        filename = f"{asset_id}.png"
        filepath = os.path.join(assets_dir, filename)

        img_bytes = generate_image_bytes(prompt, asset_id, is_bg)
        process_and_save_image(img_bytes, filepath, remove_bg=(not is_bg))
        print(f"   ✅ Generated and processed {asset_id} to {filepath}")

        generated_assets[asset_id] = filepath

    state["generated_assets"] = generated_assets
    return state
