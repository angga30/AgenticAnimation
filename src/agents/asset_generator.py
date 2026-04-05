import os
import random
from PIL import Image, ImageDraw, ImageFont
from src.core.state import ProductionState

def generate_placeholder_sprite(character_id: str, description: str, output_path: str):
    """Generates a simple colored placeholder sprite using Pillow."""
    width, height = 256, 512
    # Generate a deterministic color based on the character ID
    random.seed(character_id)
    color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))

    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw body (capsule shape)
    draw.rounded_rectangle([32, 64, width-32, height-32], radius=40, fill=color)
    # Draw head
    draw.ellipse([64, 16, width-64, 128], fill=(255, 220, 177))
    # Draw eyes
    draw.ellipse([96, 64, 112, 80], fill=(0, 0, 0))
    draw.ellipse([width-112, 64, width-96, 80], fill=(0, 0, 0))

    # Try to add text label
    try:
        draw.text((64, height//2), character_id, fill=(255, 255, 255))
    except Exception:
        pass

    img.save(output_path)
    return output_path

def asset_generator_node(state: ProductionState) -> ProductionState:
    """Reads characters from scenario and generates assets for them."""
    print("🎨 Asset Generator: Creating character sprites...")

    assets_dir = os.path.abspath("generated_assets")
    os.makedirs(assets_dir, exist_ok=True)

    generated_assets = state.get("generated_assets", {})
    scenario = state.get("scenario", {})
    characters = scenario.get("characters", [])

    for char in characters:
        char_id = char.get("id", "char_01")
        if char_id in generated_assets:
            continue

        desc = char.get("description", "A standard character")
        filename = f"{char_id}.png"
        filepath = os.path.join(assets_dir, filename)

        # In a real system, you'd call DALL-E or SD here, then use rembg.
        # We use a placeholder generator so it works without API keys.
        generate_placeholder_sprite(char_id, desc, filepath)

        generated_assets[char_id] = filepath
        print(f"   Generated asset for {char_id} at {filepath}")

    state["generated_assets"] = generated_assets
    return state
