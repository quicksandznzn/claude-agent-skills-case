#!/usr/bin/env python3
import argparse
import os
from collections.abc import Iterable
from typing import Any, Optional

import httpx

API_BASE = "https://www.v2ex.com/api/v2"


def ensure_success(payload: dict[str, Any]) -> None:
    if not payload.get("success"):
        message = payload.get("message") or "V2EX API error"
        raise RuntimeError(message)


def truncate(text: str, max_chars: Optional[int]) -> str:
    if max_chars is None or max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def pick_first(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        return str(value)
    return default


class V2EXClient:
    def __init__(self, token: str, api_base: str = API_BASE) -> None:
        self.token = token
        self.api_base = api_base

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def fetch_topic(self, client: httpx.Client, topic_id: int) -> dict[str, Any]:
        response = client.get(
            f"{self.api_base}/topics/{topic_id}",
            headers=self._headers(),
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        ensure_success(payload)
        return payload.get("result", {})

    def fetch_replies(
        self,
        client: httpx.Client,
        topic_id: int,
        max_pages: int,
        max_replies: Optional[int],
    ) -> list[dict[str, Any]]:
        replies: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            response = client.get(
                f"{self.api_base}/topics/{topic_id}/replies",
                headers=self._headers(),
                params={"p": page},
                timeout=20.0,
            )
            response.raise_for_status()
            payload = response.json()
            ensure_success(payload)
            data = payload.get("result") or []
            if not data:
                break
            replies.extend(data)
            if max_replies is not None and len(replies) >= max_replies:
                replies = replies[:max_replies]
                break
            page += 1
        return replies

    def format_topic(self, topic: dict[str, Any], max_chars: Optional[int]) -> str:
        title = pick_first(topic.get("title"))
        content = pick_first(topic.get("content"), topic.get("content_rendered"))
        node_info = topic.get("node") or {}
        member_info = topic.get("member") or {}
        node = pick_first(node_info.get("title"), node_info.get("name"), topic.get("node_id"))
        author = pick_first(
            member_info.get("username"),
            member_info.get("name"),
            member_info.get("id"),
        )
        created = pick_first(topic.get("created"), topic.get("created_at"))
        return "\n".join(
            [
                f"Title: {title}",
                f"Author: {author}",
                f"Node: {node}",
                f"Created: {created}",
                f"Content:\n{truncate(content, max_chars)}",
            ]
        ).strip()

    def format_replies(self, replies: Iterable[dict[str, Any]], max_chars: Optional[int]) -> str:
        blocks: list[str] = []
        for idx, reply in enumerate(replies, start=1):
            member_info = reply.get("member") or {}
            author = pick_first(
                member_info.get("username"),
                member_info.get("name"),
                member_info.get("id"),
            )
            created = pick_first(reply.get("created"), reply.get("created_at"))
            content = pick_first(reply.get("content"), reply.get("content_rendered"))
            block = "\n".join(
                [
                    f"[{idx}] Author: {author}",
                    f"Created: {created}",
                    f"Content:\n{truncate(content, max_chars)}",
                ]
            )
            blocks.append(block)
        return "\n\n".join(blocks).strip()

    def build_bundle(
        self,
        topic_id: int,
        max_pages: int,
        max_replies: Optional[int],
        max_chars: Optional[int],
    ) -> str:
        with httpx.Client(verify=False) as client:
            topic = self.fetch_topic(client, topic_id)
            replies = self.fetch_replies(
                client,
                topic_id,
                max_pages=max_pages,
                max_replies=max_replies,
            )
        topic_text = self.format_topic(topic, max_chars)
        replies_text = self.format_replies(replies, max_chars)
        return "\n\n".join(
            [
                "文章内容（主题）:",
                topic_text or "N/A",
                "",
                "评论:",
                replies_text or "No replies.",
            ]
        ).strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="v2ex-fetch-bundle",
        description="Fetch a V2EX topic and replies for analysis.",
    )
    parser.add_argument("--topic-id", type=int, required=True, help="V2EX topic id.")
    parser.add_argument("--max-pages", type=int, default=1, help="Max reply pages to fetch.")
    parser.add_argument(
        "--max-replies",
        type=int,
        default=0,
        help="Max replies to include (0 for no limit).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=0,
        help="Max chars per content block (0 for no limit).",
    )
    args = parser.parse_args()

    token = os.getenv("V2EX_TOKEN")
    if not token:
        raise SystemExit("Missing V2EX_TOKEN. Set V2EX_TOKEN.")

    client = V2EXClient(token)
    max_replies = args.max_replies or None
    max_chars = args.max_chars or None
    bundle = client.build_bundle(args.topic_id, args.max_pages, max_replies, max_chars)
    print(bundle)


if __name__ == "__main__":
    main()
