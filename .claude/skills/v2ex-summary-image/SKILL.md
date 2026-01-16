---
name: v2ex-summary-image
description: Generate a visual summary image from V2EX topic analysis using nanobanana (Gemini image generation). Use after v2ex-topic-analyzer to create an engaging visual summary of the discussion; requires GEMINI_API_KEY and GEMINI_API_ENDPOINT environment variables.
---

# V2EX Summary Image Generator

## Overview
Generate a visual summary image from V2EX topic analysis results using the nanobanana API (Gemini image generation model). The generated image uses a cute hand-drawn bullet journal style with cartoon characters.

## Prerequisites
- Python 3.8+
- `google-generativeai` package: `pip install google-generativeai`
- Environment variables:
  - `GEMINI_API_KEY`: API key for authentication
  - `GEMINI_API_ENDPOINT`: API endpoint URL (e.g., `http://googleapis.com`)

## Workflow
1. Collect inputs:
   - Required: `analysis_text` - The V2EX topic analysis content (typically output from v2ex-topic-analyzer)
   - Optional: `output_path` - Path to save the generated image (default: `./v2ex_summary.png`)
   - Optional: `reference_image` - Custom reference style image (default: built-in `references/style-reference.png`)

2. Generate image:
   - Run: `python3 .claude/skills/v2ex-summary-image/scripts/generate_summary_image.py --analysis "analysis text" --output ./output.png`
   - Or pipe analysis from file: `python3 .claude/skills/v2ex-summary-image/scripts/generate_summary_image.py --analysis-file ./analysis.md --output ./output.png`

3. Output:
   - Returns the path to the generated summary image
   - The image visualizes key points in a hand-drawn bullet journal style with Chinese text

## Usage Examples

### Generate with default reference style (recommended)
```bash
python3 .claude/skills/v2ex-summary-image/scripts/generate_summary_image.py \
  --analysis "## 主题概览\n这是一个关于..." \
  --output ./summary.png
```

### Generate from analysis file
```bash
python3 .claude/skills/v2ex-summary-image/scripts/generate_summary_image.py \
  --analysis-file ./v2ex_analysis.md \
  --output ./summary.png
```

### Use custom reference image
```bash
python3 .claude/skills/v2ex-summary-image/scripts/generate_summary_image.py \
  --analysis-file ./v2ex_analysis.md \
  --reference-image ./my-style.png \
  --output ./summary.png
```

### Generate without reference image
```bash
python3 .claude/skills/v2ex-summary-image/scripts/generate_summary_image.py \
  --analysis-file ./v2ex_analysis.md \
  --no-reference \
  --output ./summary.png
```

## Reference Image
The skill includes a built-in reference image at `references/style-reference.png` that defines the visual style:
- Hand-drawn bullet journal aesthetic
- Warm beige/cream paper texture background
- Cute cartoon fox mascot character
- Sticky notes, arrows, and decorative elements
- Chinese text with handwritten appearance
- Funnel diagrams and principle boxes

## Integration with v2ex-topic-analyzer
This skill is designed to be used after `v2ex-topic-analyzer`:
1. First, run `v2ex-topic-analyzer` to get the analysis
2. Save the analysis to a file or pass it directly
3. Run this skill to generate a visual summary

## Notes
- The generated image will be in PNG format
- All text in the generated image will be in Chinese (纯中文)
- Uses Gemini 2.0 Flash image generation model
- Reference image helps maintain consistent visual style across generations
