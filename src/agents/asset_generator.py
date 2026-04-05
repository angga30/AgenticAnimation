import os
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw
from rembg import remove
from openai import OpenAI
from src.core.state import ProductionState

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def fallback_generate_placeholder(asset_id: str, is_bg: bool, output_path: str):
    """Fallback generator when API fails or keys are missing."""
    width, height = (1024, 1024) if is_bg else (512, 512)
    random.seed(asset_id)

    if is_bg:
        color = (random.randint(20, 80), random.randint(20, 80), random.randint(50, 100))
        img = Image.new('RGB', (width, height), color)
        draw = ImageDraw.Draw(img)
        # Draw some background shapes
        for _ in range(5):
            x = random.randint(0, width)
            y = random.randint(0, height)
            s = random.randint(50, 300)
            draw.rectangle([x, y, x+s, y+s], outline=(255,255,255), width=2)
    else:
        color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([128, 128, width-128, height-64], radius=40, fill=color)
        draw.ellipse([192, 64, width-192, 192], fill=(255, 220, 177))
        draw.ellipse([224, 100, 240, 116], fill=(0,0,0))
        draw.ellipse([width-240, 100, width-224, 116], fill=(0,0,0))
        try:
            draw.text((128, height//2), asset_id, fill=(255, 255, 255))
        except Exception:
            pass

    img.save(output_path)
    return output_path

def generate_image_with_dalle(prompt: str, output_path: str, remove_bg: bool = False):
    client = get_openai_client()
    if not client:
        raise ValueError("No OPENAI_API_KEY available")

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    img_data = requests.get(image_url).content

    if remove_bg:
        img_data = remove(img_data)

    img = Image.open(BytesIO(img_data))
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
    print("🎨 Asset Generator: Creating assets via DALL-E & Rembg...")

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

        try:
            generate_image_with_dalle(prompt, filepath, remove_bg=(not is_bg))
            print(f"   ✅ Generated {asset_id} via LLM to {filepath}")
        except Exception as e:
            print(f"   ⚠️ LLM/API failed for {asset_id} ({e}). Falling back to placeholder.")
            fallback_generate_placeholder(asset_id, is_bg, filepath)

        generated_assets[asset_id] = filepath

    state["generated_assets"] = generated_assets
    return state
