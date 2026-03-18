"""interfaces/cli.py"""
import asyncio
from agent.research_agent import ResearchAgent
from config import Config


class CLIInterface:
    def __init__(self, agent: ResearchAgent):
        self._agent = agent

    def run(self, topic: str) -> None:
        asyncio.run(self._run_async(topic))

    async def _run_async(self, topic: str) -> None:
        output = await self._agent.run(topic, on_progress=print)
        rel = output.path.relative_to(Config.VAULT_PATH)
        print(f"\n✅ 完成！")
        print(f"   領域：{output.domain}")
        print(f"   路徑：{rel}")
        print(f"   Sync：{'✓' if output.synced else '✗ (無變更或失敗)'}")
