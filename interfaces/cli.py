"""interfaces/cli.py"""
import asyncio
from agent.research_agent import ResearchAgent
from config import Config


class CLIInterface:
    def __init__(self, agent: ResearchAgent):
        self._agent = agent

    def run(self, topic: str) -> None:
        asyncio.run(self._loop(topic))

    async def _loop(self, topic: str) -> None:
        while topic:
            output = await self._agent.run(topic, on_progress=print)
            rel = output.path.relative_to(Config.VAULT_PATH)
            print(f"\n✅ 完成！")
            print(f"   領域：{output.domain}")
            print(f"   路徑：{rel}")
            print(f"   Sync：{'✓' if output.synced else '✗ (無變更或失敗)'}")

            if not output.followups:
                break

            print("\n💡 延伸探索建議：")
            for i, t in enumerate(output.followups, 1):
                print(f"   {i}. {t}")
            print("\n輸入數字選擇，或直接輸入新主題（Enter 離開）：", end="", flush=True)

            choice = input().strip()
            if not choice:
                break
            if choice.isdigit() and 1 <= int(choice) <= len(output.followups):
                topic = output.followups[int(choice) - 1]
            else:
                topic = choice
