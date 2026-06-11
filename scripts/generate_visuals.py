"""
Generate an AI visual using DALL-E 3 based on brand DNA and style.

Usage:
    python scripts/generate_visuals.py <<'JSON'
    {
      "brand": "youmi",
      "prompt": "Minimalist representation of an agentic workflow",
      "aspect_ratio": "1:1"
    }
    JSON

Output: JSON with image_url and revised_prompt.
"""
import sys
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from notion_client import load_brand_style, classify_error

load_dotenv(Path(__file__).parent.parent / '.env')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')


def generate_visual(data: dict) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in .env")

    brand = data.get('brand')
    if not brand:
        raise ValueError('brand is required; pass the target brand explicitly')
    style = load_brand_style(brand)
    
    # Construct a high-signal prompt using Brand Style
    base_prompt = data.get('prompt', '')
    identity = style.get('visual_identity', {})
    keywords = identity.get('style_keywords', [])
    image_style = identity.get('image_style', '')
    
    style_suffix = f" Style keywords: {', '.join(keywords)}." if keywords else ""
    if image_style:
        style_suffix += f" Overall style: {image_style}"
        
    full_prompt = f"{base_prompt}. {style_suffix}"
    
    size = "1024x1024"
    if data.get('aspect_ratio') == '16:9':
        size = "1792x1024"
    elif data.get('aspect_ratio') == '9:16':
        size = "1024x1792"

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "dall-e-3",
            "prompt": full_prompt,
            "n": 1,
            "size": size,
            "quality": "standard"
        }
    )
    
    response.raise_for_status()
    result = response.json()
    
    return {
        "image_url": result['data'][0]['url'],
        "revised_prompt": result['data'][0].get('revised_prompt', ''),
        "brand": brand
    }


if __name__ == '__main__':
    try:
        data = json.loads(sys.stdin.read())
        result = generate_visual(data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e), 'kind': classify_error(e)}))
        sys.exit(1)
