---
name: v2ex-topic-analyzer
description: Analyze V2EX topic threads by fetching the topic and replies via the V2EX API v2 and producing a structured written analysis. Use when asked to analyze a V2EX topic by ID, summarize a V2EX discussion, or extract insights from a V2EX thread; requires a V2EX Personal Access Token (V2EX_TOKEN) and the bundled fetch script.
---

# V2EX Topic Analyzer

## Overview
Fetch the topic and replies with the bundled script, then write a structured analysis using the framework in `references/analysis-framework.md`.

## Workflow
1. Collect inputs:
   - Required: `topic_id`
   - Optional: `max_pages` (default 1), `max_chars` to truncate long content, `max_replies` to cap replies
   - Confirm `V2EX_TOKEN` is set in the environment.
2. Fetch data:
   - Run: `python3 .claude/skills/v2ex-topic-analyzer/scripts/fetch_v2ex_bundle.py --topic-id <id> --max-pages <n>`
   - If the bundle is too large, rerun with `--max-chars <n>` or `--max-replies <n>`.
3. Analyze:
   - Read `references/analysis-framework.md`.
   - Answer each section in order with concrete evidence from the topic and replies.
   - If information is missing, say so explicitly.
   - Write in Chinese unless the user explicitly requests another language.
4. Output:
   - Return only the analysis body in Markdown and language must be chinese.
   - Do not include a top-level title, tool logs, or the raw bundle.
