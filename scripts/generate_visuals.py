"""
Generate an AI visual using DALL-E 3 based on brand DNA.

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
from notion_client import classify_error

load_dotenv(Path(__file__).parent.parent / '.env')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')


def _load_visual_identity_from_dna(brand: str) -> str:
    """Return the Visual Identity section from brands/<brand>/DNA.md, if present."""
    dna_path = Path(__file__).parent.parent / 'brands' / brand / 'DNA.md'
    if not dna_path.exists():
        return ''

    lines = dna_path.read_text(encoding='utf-8').splitlines()
    section = []
    in_section = False
    for line in lines:
        if line.startswith('## '):
            if in_section:
                break
            in_section = line.strip().lower() == '## visual identity'
            continue
        if in_section and line.strip():
            cleaned = line.strip().lstrip('- ').strip()
            if 'DesignLore/' in cleaned or cleaned.startswith('Do not hand-edit'):
                continue
            section.append(cleaned)
    return ' '.join(section)


def generate_visual(data: dict) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in .env")

    brand = data.get('brand')
    if not brand:
        raise ValueError('brand is required; pass the target brand explicitly')

    # Construct a high-signal prompt using brand DNA; visual tokens live in DesignLore.
    base_prompt = data.get('prompt', '')
    visual_identity = _load_visual_identity_from_dna(brand)
    full_prompt = base_prompt.strip()
    if visual_identity:
        suffix = f"Brand visual direction: {visual_identity}"
        full_prompt = f"{full_prompt}. {suffix}" if full_prompt else suffix
    
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
