import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query


async def run():
    options = ClaudeAgentOptions(
        setting_sources=["user", "project"],  # Load Skills from filesystem
        allowed_tools=["Skill", "Read", "Write", "Bash"],  # Enable Skill tool
    )

    async for message in query(prompt="Write a warm greeting for Vincent.", options=options):
        print(message)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
