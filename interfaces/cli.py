"""interfaces/cli.py"""
import asyncio
from agent.research_agent import ResearchAgent
from config import Config


class CLIInterface:
    def __init__(self, agent: ResearchAgent):
        self._agent = agent

    def run(self, topic: str) -> None:
        asyncio.run(self._loop(topic))

    def run_fleeting(self, topic: str, content: str) -> None:
        asyncio.run(self._do_fleeting(topic, content))

    # ── research flow ─────────────────────────────────────────────────────

    async def _loop(self, topic: str) -> None:
        while topic:
            focus = await self._ask_aspect(topic)

            output = await self._agent.run(topic, focus=focus, on_progress=print)
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

    async def _ask_aspect(self, topic: str) -> str | None:
        """Ask the user which aspect of the topic to focus on. Returns the chosen focus or None."""
        print(f"\n💭 取得「{topic}」的研究面向建議...")
        try:
            aspects = await self._agent.suggest_aspects(topic)
        except Exception:
            return None

        if not aspects:
            return None

        print(f"\n🎯 「{topic}」有哪個面向想深入研究？")
        for i, a in enumerate(aspects, 1):
            print(f"   {i}. {a}")
        print("\n輸入數字選擇，或直接描述面向（Enter 跳過）：", end="", flush=True)

        choice = input().strip()
        if not choice:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(aspects):
            return aspects[int(choice) - 1]
        return choice

    # ── fleeting note flow ────────────────────────────────────────────────

    async def _do_fleeting(self, topic: str, content: str) -> None:
        output = await self._agent.add_fleeting(topic, content, on_progress=print)
        rel = output.path.relative_to(Config.VAULT_PATH)
        print(f"\n📝 隨手筆記已儲存！")
        print(f"   標題：{output.title}")
        print(f"   領域：{output.domain}")
        print(f"   路徑：{rel}")
        print(f"   Sync：{'✓' if output.synced else '✗ (無變更或失敗)'}")
