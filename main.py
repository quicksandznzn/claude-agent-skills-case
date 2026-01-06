from dotenv import load_dotenv

load_dotenv()

import argparse
import asyncio
import logging
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock

logger = logging.getLogger(__name__)


def build_prompt(topic_id: int, max_pages: int) -> str:
    return (
        "Analyze the V2EX topic using the v2ex-topic-analyzer skill. "
        f"topic_id={topic_id}, max_pages={max_pages}. "
        "Return only the analysis body in Markdown and language must be chinese"
    )


async def run(topic_id: int, max_pages: int, model: str | None, verbose: bool) -> str:
    def _stderr_logger(line: str) -> None:
        logger.debug("claude-cli: %s", line)

    options = ClaudeAgentOptions(
        setting_sources=["user", "project"],
        allowed_tools=["Skill", "Read", "Write", "Bash"],
        permission_mode="bypassPermissions",
        model=model,
        stderr=_stderr_logger if verbose else None,
        extra_args={"debug-to-stderr": None} if verbose else {},
    )

    chunks: list[str] = []
    final_result: str | None = None
    async for message in query(prompt=build_prompt(topic_id, max_pages), options=options):
        logger.debug(message)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
        elif isinstance(message, ResultMessage) and message.result:
            final_result = message.result

    output = "".join(chunks).strip()
    if not output and final_result:
        output = final_result.strip()
    return output


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

    analysis = asyncio.run(run(args.topic_id, args.max_pages, args.model, args.verbose))
    if not analysis:
        raise SystemExit("No analysis output received from Claude Agent SDK.")

    output_path = resolve_output_path(args.output, args.topic_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"# V2EX Analysis {args.topic_id}\n\n{analysis}\n", encoding="utf-8")
    logger.info("Saved analysis to %s", output_path)


if __name__ == "__main__":
    main()
