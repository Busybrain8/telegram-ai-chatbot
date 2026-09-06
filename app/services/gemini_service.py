import logging

from google import genai
from google.genai import types, errors

from app.config import GEMINI_API_KEY


logger = logging.getLogger(__name__)


client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"


SYSTEM_PROMPT = """
You are MyAiBot, a helpful and intelligent AI assistant on Telegram.

Your personality:
- Friendly, professional, and conversational.
- Helpful and clear in your responses.
- Be concise when a short answer is sufficient.
- Provide detailed explanations when the user asks for them.
- Do not unnecessarily repeat information.
- Ask clarifying questions when the user's request is unclear.

Conversation behavior:
- Use the conversation history to maintain context.
- Remember relevant information the user has shared during the conversation.
- When the user refers to something previously discussed, use the conversation history to understand what they mean.
- Do not claim to remember information that is not present in the conversation history.

Technical behavior:
- When providing code, use clear and properly formatted code blocks.
- Explain technical concepts in a way that matches the user's apparent level of understanding.
- If you are uncertain about something, say so rather than inventing information.

Telegram behavior:
- You are interacting with the user through Telegram.
- Keep responses readable and appropriately formatted for Telegram.
- Avoid unnecessarily long responses.
- Use emojis sparingly and only when they improve readability.
"""


async def generate_response(
    conversation_history: list[dict],
) -> str:

    logger.info(
        "Generating Gemini response: model=%s history_messages=%s",
        MODEL_NAME,
        len(conversation_history),
    )

    try:

        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=conversation_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        if not response.text:

            logger.warning(
                "Gemini returned an empty response"
            )

            raise RuntimeError(
                "Gemini returned an empty response"
            )

        logger.info(
            "Gemini response generated successfully"
        )

        return response.text

    except errors.ClientError as e:

        logger.error(
            "Gemini ClientError: %s",
            e,
        )

        if e.code == 429:

            raise RuntimeError(
                "Gemini quota exceeded"
            ) from e

        raise RuntimeError(
            "Gemini API request failed"
        ) from e

    except Exception as e:

        logger.exception(
            "Unexpected Gemini error: %s",
            e,
        )

        raise RuntimeError(
            "Unexpected Gemini error"
        ) from e