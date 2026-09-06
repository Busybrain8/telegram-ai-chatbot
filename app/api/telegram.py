from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from app.services.conversation_service import (
    clear_history,
    get_history,
    get_recent_messages,
    mark_update_processed,
    save_message,
    update_already_processed,
)
from app.services.gemini_service import generate_response
from app.services.telegram_service import (
    send_message,
    send_typing_action,
    set_webhook,
)

from app.config import TELEGRAM_WEBHOOK_SECRET

from app.core.rate_limiter import is_rate_limited

class WebhookRequest(BaseModel):
    webhook_url: str


router = APIRouter(
    prefix="/telegram",
    tags=["Telegram"],
)

logger = logging.getLogger(__name__)


@router.post("/webhook")
async def telegram_webhook(request: Request):

    try:

        secret_token = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if secret_token != TELEGRAM_WEBHOOK_SECRET:

            logger.warning(
                "Unauthorized Telegram webhook request"
            )

            return JSONResponse(
                status_code=403,
                content={
                    "status": "forbidden"
                },
            )

        update = await request.json()

        # =========================
        # Prevent Duplicate Updates
        # =========================

        update_id = update.get("update_id")

        if update_id is not None:

            if update_already_processed(update_id):

                logger.warning(
                    "Duplicate Telegram update ignored: update_id=%s",
                    update_id,
                )

                return {
                    "status": "duplicate"
                }

            mark_update_processed(update_id)

            logger.info(
                "Telegram update marked as processed: update_id=%s",
                update_id,
            )

        message = update.get("message")

        # =========================
        # Validate Telegram Update
        # =========================

        if not message:

            logger.info(
                "Ignoring Telegram update without message"
            )

            return {
                "status": "ignored"
            }

        chat = message.get("chat")

        if not chat:

            logger.info(
                "Ignoring Telegram message without chat"
            )

            return {
                "status": "ignored"
            }

        chat_id = chat["id"]

        

        text = message.get("text")

        # =========================
        # Unsupported Message Type
        # =========================

        if not text:

            logger.info(
                "Ignoring unsupported Telegram message type: chat_id=%s",
                chat_id,
            )

            await send_message(
                chat_id=chat_id,
                text=(
                    "I currently support text messages only. "
                    "Please send me a text message."
                ),
            )

            return {
                "status": "ignored"
            }

        logger.info(
            "Telegram message received: chat_id=%s text=%s",
            chat_id,
            text,
        )

        # =========================
        # Telegram Commands
        # =========================

        if text == "/start":

            logger.info(
                "Processing /start command: chat_id=%s",
                chat_id,
            )

            await send_message(
                chat_id=chat_id,
                text=(
                    "👋 Welcome to MyAiBot!\n\n"
                    "I'm your AI assistant. You can ask me "
                    "questions, have conversations, or get help "
                    "with different tasks.\n\n"
                    "Use /help to see available commands."
                ),
            )

            return {
                "status": "success"
            }

        if text == "/help":

            logger.info(
                "Processing /help command: chat_id=%s",
                chat_id,
            )

            await send_message(
                chat_id=chat_id,
                text=(
                    "🤖 MyAiBot Commands\n\n"
                    "/start - Start the bot\n"
                    "/help - Show available commands\n"
                    "/status - Check bot status\n"
                    "/history - Show recent conversation history\n"
                    "/reset - Clear your conversation history\n\n"
                    "You can also simply send me a message "
                    "and I'll respond."
                ),
            )

            return {
                "status": "success"
            }

        if text == "/status":

            logger.info(
                "Processing /status command: chat_id=%s",
                chat_id,
            )

            await send_message(
                chat_id=chat_id,
                text=(
                    "✅ MyAiBot is online.\n\n"
                    "🤖 Bot: Online\n"
                    "🧠 AI: Gemini\n"
                    "💾 Memory: Enabled\n"
                    "🌐 API: FastAPI"
                ),
            )

            return {
                "status": "success"
            }

        if text == "/reset":

            logger.info(
                "Processing /reset command: chat_id=%s",
                chat_id,
            )

            clear_history(chat_id)

            await send_message(
                chat_id=chat_id,
                text=(
                    "🧹 Your conversation history has been "
                    "cleared.\n\n"
                    "We're starting fresh!"
                ),
            )

            return {
                "status": "success"
            }


        if text == "/history":

            logger.info(
                "Processing /history command: chat_id=%s",
                chat_id,
            )

            messages = get_recent_messages(
                chat_id=chat_id,
                limit=10,
            )

            if not messages:

                await send_message(
                    chat_id=chat_id,
                    text="📭 You don't have any conversation history yet.",
                )

                return {
                    "status": "success"
                }

            history_text = "📝 Recent Conversation\n\n"

            for message in messages:

                if message.role == "user":
                    label = "You"
                else:
                    label = "MyAiBot"

                history_text += (
                    f"{label}: {message.content}\n\n"
                )

            await send_message(
                chat_id=chat_id,
                text=history_text,
            )

            return {
                "status": "success"
            }

        # =========================
        # Normal Message
        # =========================

        if is_rate_limited(chat_id):

            logger.warning(
                "Rate limit exceeded: chat_id=%s",
                chat_id,
            )

            await send_message(
                chat_id=chat_id,
                text=(
                    "⏳ You're sending messages too quickly.\n\n"
                    "Please wait a little while before trying again."
                ),
            )

            return {
                "status": "rate_limited"
            }

        save_message(
            chat_id=chat_id,
            role="user",
            content=text,
        )

        logger.info(
            "User message saved: chat_id=%s",
            chat_id,
        )

        # =========================
        # Get Conversation History
        # =========================

        history = get_history(chat_id)

        logger.info(
            "Conversation history retrieved: chat_id=%s messages=%s",
            chat_id,
            len(history),
        )

        # =========================
        # Show Typing Indicator
        # =========================

        await send_typing_action(
            chat_id=chat_id,
        )

        # =========================
        # Generate AI Response
        # =========================

        try:

            logger.info(
                "Generating AI response: chat_id=%s",
                chat_id,
            )

            ai_response = await generate_response(
                conversation_history=history,
            )

            logger.info(
                "AI response generated: chat_id=%s",
                chat_id,
            )

        except RuntimeError as e:

            logger.error(
                "Gemini error: chat_id=%s error=%s",
                chat_id,
                e,
            )

            ai_response = (
                "I'm currently experiencing high demand. "
                "Please try again in a little while."
            )

        # =========================
        # Save AI Response
        # =========================

        save_message(
            chat_id=chat_id,
            role="model",
            content=ai_response,
        )

        logger.info(
            "AI response saved: chat_id=%s",
            chat_id,
        )

        # =========================
        # Send Response to Telegram
        # =========================

        try:

            logger.info(
                "Sending response to Telegram: chat_id=%s",
                chat_id,
            )

            await send_message(
                chat_id=chat_id,
                text=ai_response,
            )

            logger.info(
                "Response sent successfully: chat_id=%s",
                chat_id,
            )

        except Exception as e:

            logger.exception(
                "Failed to send Telegram response: chat_id=%s error=%s",
                chat_id,
                e,
            )

            raise

        return {
            "status": "success"
        }

    except Exception as e:

        logger.exception(
            "Telegram webhook error: %s",
            e,
        )

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
            },
        )


# =========================
# Set Telegram Webhook
# =========================

@router.post("/set-webhook")
async def setup_webhook(request: WebhookRequest):

    logger.info(
        "Setting Telegram webhook: url=%s",
        request.webhook_url,
    )

    result = await set_webhook(
        request.webhook_url
    )

    logger.info(
        "Telegram webhook configured successfully",
    )

    return result