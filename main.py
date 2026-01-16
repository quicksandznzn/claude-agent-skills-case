from dotenv import load_dotenv

load_dotenv()

import argparse
import asyncio
import logging
import os
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    create_sdk_mcp_server,
    tool,
)

logger = logging.getLogger(__name__)


def build_prompt(topic_id: int, max_pages: int, output_path: str) -> str:
    image_output_path = output_path.replace(".md", "_summary.png")
    return (
        "Complete the following workflow step by step:\n\n"
        "## Step 1: Analyze V2EX Topic\n"
        "Use the v2ex-topic-analyzer skill to analyze the topic. "
        f"Parameters: topic_id={topic_id}, max_pages={max_pages}. "
        "The analysis should be in Markdown format and Chinese language.\n\n"
        "## Step 2: Generate Summary Image\n"
        "After completing the analysis, use the v2ex-summary-image skill to generate a visual summary. "
        f"Save the analysis text to a temp file, then run the image generator with output path: '{image_output_path}'. "
        "The image will use a hand-drawn bullet journal style with Chinese text.\n\n"
        "## Step 3: Save Final Output\n"
        "Use the write_v2ex_analysis tool to save the final result. "
        f"Parameters: topic_id={topic_id}, analysis=<your analysis with image>, output_path='{output_path}'. "
        "Insert the summary image at the beginning of the markdown:\n"
        f"![V2EX话题总结]({image_output_path})\n\n"
        "---\n\n"
        "<rest of your analysis content>"
    )


@tool(
    "write_v2ex_analysis",
    "Write V2EX analysis result to a file",
    {"topic_id": int, "analysis": str, "output_path": str},
)
async def write_v2ex_analysis(args: dict) -> dict:
    """Write V2EX analysis to a markdown file."""
    from pathlib import Path

    topic_id = args["topic_id"]
    analysis = args["analysis"]
    output_path_str = args.get("output_path", "")

    # Resolve output path
    if output_path_str:
        file_path = Path(output_path_str)
    else:
        file_path = Path("analysis_outputs") / f"analysis_{topic_id}.md"

    # Create directory and write file
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f"# V2EX Analysis {topic_id}\n\n{analysis}\n", encoding="utf-8")

    return {"content": [{"type": "text", "text": f"Analysis saved to {file_path}"}]}


# Create MCP server config
mcp_server = create_sdk_mcp_server(name="v2ex-tools", version="1.0.0", tools=[write_v2ex_analysis])


async def run(topic_id: int, max_pages: int, output_path: str, model: str | None, verbose: bool) -> None:
    def _stderr_logger(line: str) -> None:
        logger.debug("claude-cli: %s", line)

    options = ClaudeAgentOptions(
        setting_sources=["user", "project"],
        allowed_tools=["Skill", "Read", "Write", "Bash", "mcp__v2ex-tools__write_v2ex_analysis"],
        permission_mode="bypassPermissions",
        model=model,
        stderr=_stderr_logger if verbose else None,
        extra_args={"debug-to-stderr": None} if verbose else {},
        mcp_servers={"v2ex-tools": mcp_server},
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt=build_prompt(topic_id, max_pages, output_path))
        async for message in client.receive_response():
            print(message)


def resolve_output_path(output_path: str | None, topic_id: int) -> Path:
    if output_path:
        return Path(output_path)
    return Path("analysis_outputs") / f"analysis_{topic_id}.md"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="v2ex-agent",
        description="Analyze a V2EX topic with Claude Agent SDK skills.",
    )
    parser.add_argument("--topic-id", type=int, required=True, help="V2EX topic id.")
    parser.add_argument("--max-pages", type=int, default=1, help="Max reply pages to fetch.")
    parser.add_argument("--model", type=str, default=None, help="Override Claude model.")
    parser.add_argument("--output", type=str, default=None, help="Write output to this path.")
    parser.add_argument("--verbose", action="store_true", help="Log CLI and model output.")
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if not os.getenv("V2EX_TOKEN"):
        raise SystemExit("Missing V2EX_TOKEN. Set V2EX_TOKEN.")

    output_path = str(resolve_output_path(args.output, args.topic_id))
    asyncio.run(run(args.topic_id, args.max_pages, output_path, args.model, args.verbose))


if __name__ == "__main__":
    main()
