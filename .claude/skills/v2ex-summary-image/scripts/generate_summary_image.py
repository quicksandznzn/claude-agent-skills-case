#!/usr/bin/env python3
"""Generate visual summary image from V2EX topic analysis using nanobanana API."""

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import Optional

import google.generativeai as genai

SCRIPT_DIR = Path(__file__).parent
DEFAULT_REFERENCE_IMAGE = SCRIPT_DIR.parent / "references" / "style-reference.png"


def get_env_or_exit(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.getenv(name)
    if not value:
        print(f"Error: Missing required environment variable {name}", file=sys.stderr)
        sys.exit(1)
    return value


def configure_client() -> None:
    """Configure the Gemini client with nanobanana endpoint."""
    api_key = get_env_or_exit("GEMINI_API_KEY")
    api_endpoint = get_env_or_exit("GEMINI_API_ENDPOINT")

    genai.configure(
        api_key=api_key,
        transport="rest",
        client_options={"api_endpoint": api_endpoint},
    )


def load_reference_image(image_path: Path) -> dict:
    """Load reference image and return as inline data for Gemini."""
    if not image_path.exists():
        raise FileNotFoundError(f"Reference image not found: {image_path}")

    image_bytes = image_path.read_bytes()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    suffix = image_path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(suffix, "image/png")

    return {"mime_type": mime_type, "data": image_base64}


def build_prompt(analysis_text: str) -> str:
    """Build the image generation prompt from analysis text."""
    prompt = f"""Generate a cute hand-drawn bullet journal style illustration based on the reference image style.

CRITICAL STYLE REQUIREMENTS (copy exactly from reference image):
- Warm beige/cream paper texture background
- Hand-drawn sketch aesthetic with soft pastel colors (peach, light blue, cream)
- Include a cute cartoon fox or animal mascot character scattered throughout
- Use sticky notes, arrows, dashed lines, and decorative elements (stars, sparkles, brain icons)
- Funnel diagram in the center showing workflow progression
- Numbered list items on the left side with yellow sticky note style
- Principle boxes on the right side with decorative frames
- Small icons and illustrations throughout

TEXT REQUIREMENTS:
- ALL text MUST be in Chinese characters only (纯中文)
- Title should be large and decorative at the top
- Use handwritten-style Chinese font appearance

CONTENT TO ILLUSTRATE:
{analysis_text[:2500]}

Generate an image that looks like a creative, 
informative hand-drawn journal page matching the reference style exactly. The layout should have:
1. A decorative Chinese title at top center
2. Core structure list on the left (numbered 1-4)
3. A funnel/workflow diagram in the center
4. Principle boxes on the right side
5. Cute cartoon character(s) integrated into the design
6. Decorative elements like stars, icons, and dashed lines throughout"""

    return prompt


def generate_image(prompt: str, output_path: Path, reference_image_path: Optional[Path] = None) -> Path:
    """Generate image using Gemini model with optional reference image."""
    model = genai.GenerativeModel("gemini-3-pro-image")

    contents: list = []

    if reference_image_path and reference_image_path.exists():
        print(f"Using reference image: {reference_image_path}")
        ref_image_data = load_reference_image(reference_image_path)
        contents.append({"inline_data": ref_image_data})
        contents.append(
            "Above is the reference style image. "
            "Generate a NEW image in the EXACT SAME STYLE with the following content:\n\n" + prompt
        )
    else:
        contents.append(prompt)

    response = model.generate_content(
        contents,
        generation_config={"response_modalities": ["TEXT", "IMAGE"]},
    )

    if not response.candidates:
        raise RuntimeError("No response candidates returned from API")

    candidate = response.candidates[0]

    for part in candidate.content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_data = part.inline_data.data
            if isinstance(image_data, str):
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)
            return output_path

    if hasattr(response, "text") and response.text:
        raise RuntimeError(f"API returned text instead of image: {response.text[:200]}")

    raise RuntimeError("No image data found in API response")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="generate-summary-image",
        description="Generate visual summary image from V2EX topic analysis.",
    )
    parser.add_argument(
        "--analysis",
        type=str,
        help="Analysis text to visualize.",
    )
    parser.add_argument(
        "--analysis-file",
        type=str,
        help="Path to file containing analysis text.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./v2ex_summary.png",
        help="Output path for the generated image.",
    )
    parser.add_argument(
        "--reference-image",
        type=str,
        help="Path to reference style image (default: built-in style-reference.png).",
    )
    parser.add_argument(
        "--no-reference",
        action="store_true",
        help="Disable reference image, generate without style guide.",
    )

    args = parser.parse_args()

    if args.analysis:
        analysis_text = args.analysis
    elif args.analysis_file:
        analysis_path = Path(args.analysis_file)
        if not analysis_path.exists():
            print(f"Error: Analysis file not found: {args.analysis_file}", file=sys.stderr)
            sys.exit(1)
        analysis_text = analysis_path.read_text(encoding="utf-8")
    else:
        print("Error: Either --analysis or --analysis-file is required", file=sys.stderr)
        sys.exit(1)

    if not analysis_text.strip():
        print("Error: Analysis text is empty", file=sys.stderr)
        sys.exit(1)

    reference_image_path: Optional[Path] = None
    if not args.no_reference:
        if args.reference_image:
            reference_image_path = Path(args.reference_image)
        elif DEFAULT_REFERENCE_IMAGE.exists():
            reference_image_path = DEFAULT_REFERENCE_IMAGE

    configure_client()

    prompt = build_prompt(analysis_text)
    output_path = Path(args.output)

    result_path = generate_image(prompt, output_path, reference_image_path)
    print(f"Image generated successfully: {result_path}")


if __name__ == "__main__":
    main()
