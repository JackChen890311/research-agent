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

# ctx.user_data keys
_K_PENDING_TOPIC    = "pending_topic"     # topic waiting for aspect selection
_K_FLEETING_STEP    = "fleeting_step"     # "await_topic" | "await_content"
_K_FLEETING_TOPIC   = "fleeting_topic"   # topic captured in fleeting flow


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
        self._app.add_handler(CommandHandler("help",     self._on_help))
        self._app.add_handler(CommandHandler("fleeting", self._on_fleeting_cmd))
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

        text = update.message.text.strip()
        user = _username(update)

        # ── fleeting note multi-step flow ─────────────────────────────────
        fleeting_step = ctx.user_data.get(_K_FLEETING_STEP)

        if fleeting_step == "await_topic":
            ctx.user_data[_K_FLEETING_TOPIC] = text
            ctx.user_data[_K_FLEETING_STEP]  = "await_content"
            await update.message.reply_text(
                "✏️ 請輸入筆記內容（原文保留，不會修改）：",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        if fleeting_step == "await_content":
            topic = ctx.user_data.pop(_K_FLEETING_TOPIC, text)
            ctx.user_data.pop(_K_FLEETING_STEP)
            log.info("%s → fleeting「%s」", user, topic)
            await self._save_fleeting(update, topic, text)
            return

        # ── research flow: check if we're waiting for an aspect ───────────
        pending_topic = ctx.user_data.get(_K_PENDING_TOPIC)
        if pending_topic:
            ctx.user_data.pop(_K_PENDING_TOPIC)
            focus = text
            log.info("%s → 「%s」面向：「%s」", user, pending_topic, focus)
            await self._run_research(update, pending_topic, focus)
        else:
            # New topic — ask which aspect to focus on
            topic = text
            log.info("%s → 新主題「%s」", user, topic)
            await update.message.reply_text("💭 思考研究面向...", reply_markup=ReplyKeyboardRemove())
            try:
                aspects = await self._agent.suggest_aspects(topic)
                ctx.user_data[_K_PENDING_TOPIC] = topic
                await self._send_aspects(update.message, topic, aspects)
            except Exception as e:
                log.error("❌ 無法取得面向建議：%s", e)
                await self._run_research(update, topic, None)

    async def _on_fleeting_cmd(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user.id not in Config.ALLOWED_USERS:
            await update.message.reply_text("⛔ 未授權")
            return
        # Clear any in-progress research state
        ctx.user_data.pop(_K_PENDING_TOPIC, None)
        ctx.user_data[_K_FLEETING_STEP] = "await_topic"
        await update.message.reply_text(
            "📝 *隨手筆記模式*\n\n請輸入筆記主題：",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown",
        )

    # ── research helpers ──────────────────────────────────────────────────

    async def _run_research(
        self,
        update: Update,
        topic: str,
        focus: str | None,
    ) -> None:
        await update.message.reply_text("🔍", reply_markup=ReplyKeyboardRemove())
        status = await update.message.reply_text("⏳ 開始研究...")

        async def progress(msg: str):
            log.info("  %s", msg)
            await status.edit_text(msg)

        try:
            output = await self._agent.run(topic, focus=focus, on_progress=progress)
            rel    = output.path.relative_to(Config.VAULT_PATH)
            log.info("✅ 「%s」完成 → %s", output.topic, rel)
            await status.edit_text(
                f"✅ *{output.topic}*\n"
                f"📂 領域：{output.domain}\n"
                f"📄 `{rel}`",
                parse_mode="Markdown",
            )
            await self._send_followups(update.message, output.followups)
        except Exception as e:
            log.error("❌ 「%s」失敗：%s", topic, e)
            await status.edit_text(f"❌ 錯誤：{e}")

    async def _save_fleeting(self, update: Update, topic: str, content: str) -> None:
        status = await update.message.reply_text("⏳ 儲存隨手筆記...")

        async def progress(msg: str):
            log.info("  %s", msg)
            await status.edit_text(msg)

        try:
            output = await self._agent.add_fleeting(topic, content, on_progress=progress)
            rel    = output.path.relative_to(Config.VAULT_PATH)
            log.info("✅ fleeting「%s」完成 → %s", output.title, rel)
            await status.edit_text(
                f"📝 *{output.title}*\n"
                f"📂 領域：{output.domain}\n"
                f"📄 `{rel}`",
                parse_mode="Markdown",
            )
        except Exception as e:
            log.error("❌ fleeting 失敗：%s", e)
            await status.edit_text(f"❌ 錯誤：{e}")

    # ── keyboard helpers ──────────────────────────────────────────────────

    async def _send_aspects(self, message, topic: str, aspects: list[str]) -> None:
        keyboard = [[KeyboardButton(a)] for a in aspects]
        await message.reply_text(
            f"🎯 「*{topic}*」有哪個面向想深入研究？",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
            parse_mode="Markdown",
        )

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
            "📚 *NoteBoi*\n\n"
            "*隨手筆記*（輸入 /fleeting）：\n"
            "• 記下任何想法，系統自動分類儲存\n"
            "• 內容原文保留，不會修改\n\n"
            "*研究模式*（直接傳主題名稱）：\n"
            "• `間歇性斷食`\n"
            "• `卡片盒筆記法`\n\n"
            "筆記自動存入知識庫（Obsidian）並同步至雲端（Git）。",
            parse_mode="Markdown",
        )
