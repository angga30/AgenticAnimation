import os
import random
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw

def _fallback_generate_placeholder(asset_id: str, is_bg: bool) -> bytes:
    """Fallback generator when API fails or keys are missing. Returns raw bytes."""
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

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _generate_openai(prompt: str) -> bytes:
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    response = client.images.generate(
        model=os.environ.get("OPENAI_IMAGE_MODEL", "dall-e-3"),
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    return requests.get(image_url).content

def _generate_google(prompt: str) -> bytes:
    # Requires google-genai library or direct REST to Vertex/Gemini
    # This is a stub placeholder that users can fill with proper GCP Imagen logic.
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set.")
    # Implement Imagen REST/SDK call here
    raise NotImplementedError("Google Imagen logic not implemented yet.")

def _generate_custom_rest(prompt: str) -> bytes:
    """
    Generic REST endpoint provider to support custom Open Source APIs (like Qwen, Wan2.6, Banana endpoints).
    Expects CUSTOM_IMAGE_ENDPOINT and optional CUSTOM_IMAGE_API_KEY.
    """
    endpoint = os.environ.get("CUSTOM_IMAGE_ENDPOINT")
    if not endpoint:
        raise ValueError("CUSTOM_IMAGE_ENDPOINT is not set.")

    api_key = os.environ.get("CUSTOM_IMAGE_API_KEY", "")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    # Typically, custom APIs return base64 data or a URL
    if "data" in data and len(data["data"]) > 0:
        result = data["data"][0]
        if "b64_json" in result:
            return base64.b64decode(result["b64_json"])
        elif "url" in result:
            return requests.get(result["url"]).content

    raise ValueError(f"Unexpected response format from custom endpoint: {data}")

def generate_image_bytes(prompt: str, asset_id: str, is_bg: bool) -> bytes:
    """
    Agnostic image generation factory.
    Reads IMAGE_PROVIDER environment variable ('openai', 'google', 'custom', 'fallback').
    Default is 'openai'. If a provider fails, falls back to placeholder shapes automatically.
    """
    provider = os.environ.get("IMAGE_PROVIDER", "openai").lower()

    try:
        if provider == "openai":
            return _generate_openai(prompt)
        elif provider == "google":
            return _generate_google(prompt)
        elif provider == "custom":
            return _generate_custom_rest(prompt)
        elif provider == "fallback":
            return _fallback_generate_placeholder(asset_id, is_bg)
        else:
            print(f"⚠️ Image Factory: Unknown provider '{provider}'. Using fallback.")
            return _fallback_generate_placeholder(asset_id, is_bg)
    except Exception as e:
        print(f"⚠️ Image Factory ({provider}) failed: {e}. Using fallback.")
        return _fallback_generate_placeholder(asset_id, is_bg)
