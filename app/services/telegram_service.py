import logging

import httpx

from app.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_WEBHOOK_SECRET,
)

from app.utils.telegram_utils import split_message

logger = logging.getLogger(__name__)


TELEGRAM_API_URL = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
)


async def get_bot_info() -> dict:

    logger.info("Getting Telegram bot information")

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{TELEGRAM_API_URL}/getMe"
        )

        response.raise_for_status()

        return response.json()


async def send_message(
    chat_id: int,
    text: str,
) -> dict:

    logger.info(
        "Sending Telegram message to chat_id=%s",
        chat_id,
    )

    message_chunks = split_message(text)

    logger.info(
        "Message split into %s chunk(s): chat_id=%s",
        len(message_chunks),
        chat_id,
    )

    results = []

    async with httpx.AsyncClient() as client:

        for index, chunk in enumerate(
            message_chunks,
            start=1,
        ):

            logger.info(
                "Sending message chunk %s/%s: chat_id=%s",
                index,
                len(message_chunks),
                chat_id,
            )

            response = await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                },
            )

            if response.is_error:

                logger.error(
                    "Telegram API error: status=%s body=%s",
                    response.status_code,
                    response.text,
                )

            response.raise_for_status()

            results.append(
                response.json()
            )

    logger.info(
        "Telegram message sent successfully: "
        "chat_id=%s chunks=%s",
        chat_id,
        len(message_chunks),
    )

    return results[-1]


async def send_typing_action(
    chat_id: int,
) -> dict:

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{TELEGRAM_API_URL}/sendChatAction",
            json={
                "chat_id": chat_id,
                "action": "typing",
            },
        )

        response.raise_for_status()

        return response.json()

async def set_webhook(
    webhook_url: str,
) -> dict:

    logger.info(
        "Setting Telegram webhook: %s",
        webhook_url,
    )

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{TELEGRAM_API_URL}/setWebhook",
            json={
                "url": webhook_url,
                "secret_token": TELEGRAM_WEBHOOK_SECRET,
            },
        )

        if response.is_error:

            logger.error(
                "Telegram webhook error: status=%s body=%s",
                response.status_code,
                response.text,
            )

        response.raise_for_status()

        logger.info(
            "Telegram webhook set successfully",
        )

        return response.json()


async def get_webhook_info() -> dict:

    logger.info(
        "Getting Telegram webhook information"
    )

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{TELEGRAM_API_URL}/getWebhookInfo"
        )

        response.raise_for_status()

        return response.json()