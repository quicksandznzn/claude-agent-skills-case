V2EX topic analyzer CLI using Claude Agent SDK skills.

Setup
- Create a V2EX Personal Access Token (PAT) and set `V2EX_TOKEN`.
- Optional: set `LOG_LEVEL` (default INFO).

Install deps (uv)
```
uv sync
```

Usage
```
uv run v2ex-agent --topic-id 12345

# or without installing the script entrypoint
uv run python main.py --topic-id 12345
```

Output
```
analysis_outputs/analysis_12345.md
```

Useful flags
```
--max-pages 5
--output analysis_outputs/custom.md
--model claude-3-7-sonnet-20250219
--verbose
```

Notes
- The analysis is requested in Chinese by default.
- `.claude/skills/v2ex-topic-analyzer` contains the skill workflow and fetch script.
