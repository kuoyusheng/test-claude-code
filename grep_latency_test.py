import asyncio
import time
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, HookMatcher

# Correlate Grep calls even if several run in parallel
_grep_starts_ns: dict[str, int] = {}

async def pre_grep(input_data: dict, tool_use_id: str | None, _ctx):
    if input_data.get("tool_name") == "Grep" and tool_use_id:
        _grep_starts_ns[tool_use_id] = time.perf_counter_ns()
    return {}

async def post_grep(input_data: dict, tool_use_id: str | None, _ctx):
    if input_data.get("tool_name") == "Grep" and tool_use_id:
        start = _grep_starts_ns.pop(tool_use_id, None)
        if start is not None:
            ms = (time.perf_counter_ns() - start) / 1e6
            pat = input_data.get("tool_input", {}).get("pattern")
            path = input_data.get("tool_input", {}).get("path")
            glob = input_data.get("tool_input", {}).get("glob")
            output_mode = input_data.get("tool_input", {}).get("output_mode", "files_with_matches")
            print(f"[Grep] {ms:.1f} ms  pattern={pat!r}  path={path!r}  glob={glob!r}  mode={output_mode!r}")
    return {}

async def main():
    # Use current working directory for testing
    current_dir = "/Users/yu-shengkuo/projects/datagendev/marketing/"

    options = ClaudeCodeOptions(
        cwd=current_dir,
        allowed_tools=["Grep"],   # optional: avoid other tools skewing timing
        hooks={
            "PreToolUse":  [HookMatcher(matcher="Grep", hooks=[pre_grep])],
            "PostToolUse": [HookMatcher(matcher="Grep", hooks=[post_grep])],
        },
    )

    async with ClaudeSDKClient(options=options) as client:
        print("Starting grep latency tests...")

        # Test 1: Simple pattern search
        print("\n=== Test 1: Simple pattern search ===")
        await client.query("Search for 'datagen' in all .md files")
        async for _ in client.receive_response():
            pass

        # # Test 2: Regex pattern search
        # print("\n=== Test 2: Regex pattern search ===")
        # await client.query("Search for functions with pattern 'def\\s+\\w+' in Python files")
        # async for _ in client.receive_response():
        #     pass

        # # Test 3: Search with context lines
        # print("\n=== Test 3: Search with context lines ===")
        # await client.query("Search for 'async' with 2 lines of context in Python files")
        # async for _ in client.receive_response():
        #     pass

        # # Test 4: Case insensitive search
        # print("\n=== Test 4: Case insensitive search ===")
        # await client.query("Search for 'MAIN' case insensitively in all files")
        # async for _ in client.receive_response():
        #     pass

        # print("\n=== Grep latency tests completed ===")

if __name__ == "__main__":
    asyncio.run(main())