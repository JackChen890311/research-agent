"""interfaces/telegram_bot.py"""
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes,
)
from agent.research_agent import ResearchAgent
from config import Config


class TelegramBotInterface:
    def __init__(self, agent: ResearchAgent):
        self._agent = agent
        self._app = (
            ApplicationBuilder()
            .token(Config.TELEGRAM_TOKEN)
            .build()
        )
        self._app.add_handler(CommandHandler("help", self._on_help))
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )

    def run(self) -> None:
        print("🤖 Telegram Bot 啟動中...")
        self._app.run_polling()

    # ── handlers ─────────────────────────────────────────────────────────────

    async def _on_message(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user.id not in Config.ALLOWED_USERS:
            await update.message.reply_text("⛔ 未授權")
            return

        topic  = update.message.text.strip()
        status = await update.message.reply_text("⏳ 開始研究...")

        async def progress(msg: str):
            await status.edit_text(msg)

        try:
            output = await self._agent.run(topic, on_progress=progress)
            rel    = output.path.relative_to(Config.VAULT_PATH)
            await status.edit_text(
                f"✅ *{topic}*\n"
                f"📂 領域：{output.domain}\n"
                f"📄 `{rel}`",
                parse_mode="Markdown",
            )
        except Exception as e:
            await status.edit_text(f"❌ 錯誤：{e}")

    async def _on_help(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "📚 *Research Agent*\n\n"
            "直接傳主題名稱，例如：\n"
            "• `間歇性斷食`\n"
            "• `複利效應`\n"
            "• `認知偏誤`\n\n"
            "筆記自動存入 Obsidian 並 git sync。",
            parse_mode="Markdown",
        )
