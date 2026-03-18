"""main.py — Composition Root: 在這裡組裝所有元件"""
import argparse

from config import Config
from llm import create_llm_client
from search.tavily_handler import TavilySearchHandler
from agent.research_agent import ResearchAgent
from interfaces.cli import CLIInterface
from interfaces.telegram_bot import TelegramBotInterface


def build_agent() -> ResearchAgent:
    """Factory：根據 config 組裝 agent，只在這裡知道具體實作"""
    return ResearchAgent(
        llm    = create_llm_client(),
        search = TavilySearchHandler(),
        vault  = Config.VAULT_PATH,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent")
    parser.add_argument("--bot",   action="store_true", help="啟動 Telegram Bot")
    parser.add_argument("--topic", type=str,            help="CLI 模式：直接研究一個主題")
    args = parser.parse_args()

    agent = build_agent()

    if args.bot:
        TelegramBotInterface(agent).run()
    elif args.topic:
        CLIInterface(agent).run(args.topic)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
