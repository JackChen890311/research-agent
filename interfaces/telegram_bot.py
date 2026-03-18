"""interfaces/telegram_bot.py"""
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, filters, ContextTypes,
)
from agent.research_agent import ResearchAgent
from config import Config

log = logging.getLogger(__name__)


def _username(update: Update) -> str:
    u = update.effective_user
    return f"@{u.username}" if u.username else u.first_name or str(u.id)


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
        logging.basicConfig(
            format="%(asctime)s [BOT] %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
        )
        log.info("啟動，監聽中...")
        self._app.run_polling()

    # ── handlers ─────────────────────────────────────────────────────────────

    async def _on_message(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user.id not in Config.ALLOWED_USERS:
            log.warning("未授權存取：%s (id=%s)", _username(update), update.effective_user.id)
            await update.message.reply_text("⛔ 未授權")
            return

        topic = update.message.text.strip()
        user  = _username(update)
        log.info("%s → 「%s」", user, topic)
        await update.message.reply_text("🔍", reply_markup=ReplyKeyboardRemove())
        status = await update.message.reply_text("⏳ 開始研究...")

        async def progress(msg: str):
            log.info("  %s", msg)
            await status.edit_text(msg)

        try:
            output = await self._agent.run(topic, on_progress=progress)
            rel    = output.path.relative_to(Config.VAULT_PATH)
            log.info("✅ 「%s」完成 → %s", topic, rel)
            await status.edit_text(
                f"✅ *{topic}*\n"
                f"📂 領域：{output.domain}\n"
                f"📄 `{rel}`",
                parse_mode="Markdown",
            )
            await self._send_followups(update.message, output.followups)
        except Exception as e:
            log.error("❌ 「%s」失敗：%s", topic, e)
            await status.edit_text(f"❌ 錯誤：{e}")

    async def _send_followups(self, message, followups: list[str]) -> None:
        if not followups:
            return
        keyboard = [[KeyboardButton(t)] for t in followups]
        await message.reply_text(
            "💡 *延伸探索建議（點選即可研究）：*",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
            parse_mode="Markdown",
        )

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
