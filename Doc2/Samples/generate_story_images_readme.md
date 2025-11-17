# Story Images Generator

A Python script for generating sequential storytelling images for video production. The script processes segment definitions from Markdown files, generates AI-powered images using Replicate (with negative prompts to avoid text), verifies images have no text/labels using GPT-4o-mini vision model, and creates comprehensive generation reports.

## Features

- **Batch Processing**: Process multiple segments from a single `segments.md` file
- **Parallel Processing**: All segments are processed in parallel for faster execution
- **Progress Tracking**: Real-time progress bar showing `[X/Y segments complete]`
- **Dry-Run Mode**: Validate segments, preview output, and see cost estimates without generating images
- **AI Image Generation**: Uses Flux-dev (quality) or Flux-schnell (fast) models via Replicate
  - **Negative Prompts**: Automatically applied to prevent text/label generation
  - **Visual Guidance Filtering**: Removes text-related terms from prompts
  - **SDXL Fallback**: Automatically falls back to SDXL if Flux fails
- **Image Verification**: Automatically verifies images have no text/labels using GPT-4o-mini (cheapest paid vision model)
- **Retry Failed Segments**: Use `--retry-failed` to retry only failed segments from previous runs
- **Verbose Logging**: Use `--verbose` for detailed API requests, responses, timing, and prompts
- **Style Consistency**: Maintains visual consistency across images using diagram references
- **Comprehensive Reporting**: Generates detailed cost and time reports per segment and template
  - Includes failed segments with error messages
  - Cost estimates in dry-run mode
- **Error Handling**: Validates all segments before processing, keeps successful segments on failure
- **Filesystem Safety**: Sanitizes filenames and handles existing folders gracefully

## Prerequisites

- Python 3.7+
- Required Python packages:
  - `requests`
  - `Pillow` (PIL)
  - `python-dotenv` (optional, for .env file support)

Install dependencies:
```bash
pip install requests pillow python-dotenv
```

## Environment Setup

**IMPORTANT:** Before running the script, you must create a `.env` file in the same directory as the script (`Doc2/Samples/`) with your API keys.

### Required API Keys

The script requires two API keys:

1. **OPENROUTER_API_KEY** - Used for image verification (GPT-4o-mini vision model)
   - Get your key from: https://openrouter.ai/
   
2. **REPLICATE_KEY** - Used for image generation (Flux-dev, Flux-schnell, SDXL models)
   - Get your key from: https://replicate.com/

### Creating the .env File

Create a file named `.env` in `Doc2/Samples/` with the following content:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
REPLICATE_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Replace the placeholder values with your actual API keys. The script will automatically load these keys from the `.env` file when it runs.

## Usage

### Dry-Run Mode (Validation Only)

Validate `segments.md`, see cost estimates, and preview what would be generated without actually generating images:

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --dry-run
```

Dry-run mode shows:
- Validation results for all segments
- Total estimated cost (worst-case scenario)
- Per-segment cost breakdown
- Per-image cost breakdown
- Planned folder structure

### Processing Segments from Markdown File (Recommended)

Process all segments from a `segments.md` file (segments are processed in parallel):

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --num-images 2 \
  --max-verification-passes 2
```

### Processing a Single Segment Directory

Process a single segment that already has a `segment.json` file:

```bash
python Doc2/Samples/generate_story_images.py \
  --directory "Doc2/Samples/Photosynthesis/1. Hook" \
  --num-images 3 \
  --max-passes 5
```

### Using Topic Name

Process a topic from the Samples folder:

```bash
python Doc2/Samples/generate_story_images.py \
  --topic Photosynthesis \
  --num-images 2 \
  --fast
```

## Command-Line Arguments

### Required (when using `--segments`)
- `--segments PATH`: Path to `segments.md` file (processes all segments)
- `--diagram PATH`: Path to diagram.png file (required when using `--segments`)

### Optional
- `--directory PATH`: Full path to directory containing `segment.json` (takes precedence over `--topic`)
- `--topic NAME`: Topic name (searches in Samples folder, used if `--directory` not provided)
- `--num-images N`: Number of sequential images to generate per segment (default: 3)
- `--max-passes N`: Maximum regeneration attempts per image if verification fails (default: 5)
  - **Recommended**: Use 5+ passes for better success rate with text avoidance
- `--max-verification-passes N`: Maximum verification API attempts per image (default: 5)
- `--fast`: Use fast/cheap model (`flux-schnell`) instead of quality model (`flux-dev`)
- `--dry-run`: Validate `segments.md`, show cost estimates, and preview output without generating images
- `--retry-failed`: Retry only failed segments from the last run (reads from `generation_report.json`)
- `--verbose`: Enable detailed logging (API requests/responses, timing, full prompts)

## Segments.md Format

The script expects a `segments.md` file with the following format:

```markdown
Template: TemplateName

**Segment 1: Segment Title (0-10 seconds)**

- Duration badge: "10s"
- Narration text (editable textarea):
  ```
  "Your narration text here"
  ```
- Visual guidance preview: "Description of visual guidance"
- Visual guidance: "Additional visual guidance"  # Optional, will be concatenated

**Segment 2: Another Segment (10-25 seconds)**
...
```

### Format Requirements

- **Template line**: Must start with `Template: ` followed by the template name
- **Segment headers**: Format `**Segment X: Title (start-end seconds)**`
- **Duration**: Calculated from the time range in parentheses (e.g., `(0-10 seconds)` = 10 seconds)
- **Narration text**: Must be enclosed in triple backticks (```)
- **Visual guidance**: Can appear as "Visual guidance preview:" or "Visual guidance:" (both will be concatenated)

### Validation Rules

The script validates all segments before processing:
- ✅ No duplicate segment numbers
- ✅ All segments have narration text
- ✅ All segments have visual guidance
- ✅ Segments are sorted by number before processing

## Output Structure

When processing `segments.md`, the script creates the following structure:

```
{TemplateName}/
├── diagram.png                    # Copied/converted diagram reference
├── generation_report.json         # Template-level summary report
├── 1. {Segment Title}/
│   ├── segment1.json              # Segment metadata
│   └── generated_images/
│       ├── story_image_01.png
│       ├── story_image_02.png
│       └── generation_report.json # Segment-level detailed report
├── 2. {Segment Title}/
│   └── ...
└── ...
```

### Folder Naming

- If a template folder already exists, the script creates `{TemplateName}_1`, `{TemplateName}_2`, etc. (up to 100 attempts)
- Segment folders follow the same pattern if they already exist
- All filenames are sanitized to be filesystem-safe (invalid characters replaced with underscores)

## Segment JSON Format

Each segment directory contains a `segment{number}.json` file:

```json
{
    "duration": 10,
    "narrationtext": "Your narration text here",
    "visual_guidance_preview": "Visual guidance description"
}
```

## Generation Reports

### Segment-Level Report

Located at: `{Segment}/generated_images/generation_report.json`

Contains:
- Summary (total images, cost, time)
- Cost breakdown (generation vs verification)
- Time breakdown (generation vs verification vs waiting)
- Per-image details (model used, prompt snippets, verification results, retries, confidence scores)

### Template-Level Report

Located at: `{Template}/generation_report.json`

Contains:
- Template summary (aggregated totals across all segments)
- Per-segment summaries (only successful segments)
- **Failed segments list**: Segment numbers, titles, and error messages
- Full detailed data from each segment's report

### Report Backup

If a report already exists, it's automatically backed up with a timestamp:
- `generation_report_20241201_143022.json`

## Image Generation Process

For each image, the script follows this process:

1. **Generate Base Image**: Uses Replicate API (Flux-dev or Flux-schnell)
   - Includes style reference from diagram if available
   - **Negative Prompts**: Automatically applied to Flux models to prevent text/label generation
   - **Visual Guidance Filtering**: Removes text-related terms (e.g., "text overlay") from prompts
   - **Strong NO TEXT Instructions**: Prompts explicitly state "NO TEXT, NO LABELS, NO WORDS..."
   - Falls back to SDXL (with negative prompts) if primary model fails after 2 attempts

2. **Verify Image**: Uses GPT-4o-mini vision model via OpenRouter
   - Checks for text, labels, annotations
   - Retries verification up to `--max-verification-passes` times
   - Regenerates image if verification fails (up to `--max-passes` times)
   - No rate limit issues (paid tier with high limits)

3. **Save & Report**: Saves verified image and records metadata

## Cost Estimation

The script uses approximate cost rates:

- **flux-dev**: ~$0.0035 per image
- **flux-schnell**: ~$0.003 per image
- **sdxl**: ~$0.0029 per image (fallback model)
- **gpt-4o-mini-verification**: ~$0.00015 per verification (cheapest paid vision model)

**Typical costs per image** (with 5 max passes):
- Generation: ~$0.007-0.010 (includes retries)
- Verification: ~$0.0003-0.0006 (includes retries)
- **Total**: ~$0.007-0.011 per successfully generated image

Costs are tracked per image, per segment, and per template in the reports. Use `--dry-run` to see cost estimates before generating.

## Error Handling

### Validation Errors

The script validates all segments before processing:
- Missing narration text → Exit with error
- Missing visual guidance → Exit with error
- Duplicate segment numbers → Exit with error
- Missing diagram (when required) → Exit with error

### Processing Errors

- **Segment generation failure**: All partial results are cleaned up
- **Keyboard interrupt (Ctrl+C)**: Exits immediately and cleans up partial results
- **Diagram conversion failure**: Exits with error
- **API errors**: Retries with exponential backoff, falls back to alternative models

### Cleanup Behavior

On failure or interruption:
- **Keyboard interrupt (Ctrl+C)**: All created segment folders are removed
- **Segment generation failure**: Only failed segment folders are removed (successful segments are kept)
- Template directory is removed if empty or only contains diagram
- Existing reports are preserved (backed up with timestamps)

## Examples

### Example 1: Validate segments.md before generating

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --dry-run
```

### Example 2: Generate 2 images per segment with fast mode

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --num-images 2 \
  --max-verification-passes 3 \
  --fast
```

### Example 3: Generate 3 images with quality model and more retries

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --num-images 3 \
  --max-passes 5 \
  --max-verification-passes 3
```

### Example 4: Retry failed segments from previous run

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --retry-failed \
  --num-images 1 \
  --max-passes 5
```

### Example 5: Verbose mode for debugging

```bash
python Doc2/Samples/generate_story_images.py \
  --segments "Doc2/Samples/segments.md" \
  --diagram "Doc2/Samples/Photosynthesis/diagram.png" \
  --num-images 1 \
  --verbose
```

### Example 6: Process single segment directory

```bash
python Doc2/Samples/generate_story_images.py \
  --directory "Doc2/Samples/Photosynthesis/1. Hook" \
  --num-images 2 \
  --max-passes 5
```

## Tips

1. **Use `--dry-run` first**: Always validate your `segments.md` file with `--dry-run` to see cost estimates and catch errors
2. **Use 5+ max passes**: For better success rate with text avoidance, use `--max-passes 5` or higher
3. **Start with `--fast` mode**: Use `--fast` for initial testing to save costs (flux-schnell is cheaper)
4. **Visual guidance**: Avoid mentioning "text overlay" or "labels" in visual guidance - the script filters these, but it's better to avoid them
5. **Check reports**: Review `generation_report.json` files for detailed cost and time breakdowns, including failed segments
6. **Retry failed segments**: Use `--retry-failed` to retry only segments that failed in the last run
7. **Verbose mode**: Use `--verbose` to debug issues with API calls, timing, or prompt generation
8. **Diagram reference**: Always provide a diagram for style consistency across images
9. **Parallel processing**: All segments process in parallel, so progress may appear interleaved - this is normal
10. **Text avoidance**: The script uses multiple strategies to avoid text:
    - Negative prompts on all models
    - Visual guidance filtering
    - Strong NO TEXT instructions in prompts
    - Multiple regeneration attempts

## Troubleshooting

### "OPENROUTER_API_KEY not found" or "REPLICATE_KEY not found"
- Ensure `.env` file exists in the same directory as the script (`Doc2/Samples/`)
- Check that both `OPENROUTER_API_KEY` and `REPLICATE_KEY` are set in the `.env` file
- Verify the keys are on separate lines and formatted correctly:
  ```env
  OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  REPLICATE_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```
- Make sure there are no extra spaces or quotes around the key values

### "Validation failed"
- Check that all segments have narration text and visual guidance
- Verify no duplicate segment numbers exist
- Ensure segment headers follow the correct format

### "Rate limited"
- GPT-4o-mini has high rate limits (paid tier), so this should be rare
- The script automatically retries with exponential backoff
- If you see rate limits, wait a few minutes and try again
- Consider using `--fast` mode to reduce API usage

### "Text/annotations detected"
- The script uses multiple strategies to avoid text (negative prompts, filtered guidance, NO TEXT instructions)
- Increase `--max-passes` to allow more regeneration attempts (recommended: 5+)
- Check the generated images manually - sometimes the verification is overly strict
- Some segments may need more attempts than others

### "Failed to convert/copy diagram"
- Ensure diagram file exists and is readable
- Check file format (PNG, JPG, GIF supported)
- Verify file permissions

## License

[Add your license information here]

## Support

[Add support/contact information here]

