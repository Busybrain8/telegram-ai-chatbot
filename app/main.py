import logging
from fastapi.responses import JSONResponse

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.telegram import router as telegram_router
from app.database import models
from app.database.database import Base, engine
from app.services.conversation_service import (
    get_history,
    save_message,
)
from app.services.gemini_service import generate_response
from app.services.telegram_service import (
    get_bot_info,
    get_webhook_info,
)



logger = logging.getLogger(__name__)


# =========================
# Logging Configuration
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# Create Database Tables
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# FastAPI Application
# =========================

app = FastAPI(
    title="Telegram AI Chatbot",
    description="Intelligent Telegram chatbot powered by Gemini and FastAPI",
    version="1.0.0",
)




app.include_router(telegram_router)


# =========================
# Chat Request Model
# =========================

class ChatRequest(BaseModel):
    chat_id: int
    message: str


# =========================
# Root
# =========================

@app.get("/")
async def root():

    return {
        "message": "Telegram AI Chatbot API is running"
    }


# =========================
# Health Check
# =========================

@app.get("/health")
async def health_check():

    return {
        "status": "healthy"
    }


# =========================
# Chat Endpoint
# =========================

@app.post("/chat")
async def chat(request: ChatRequest):

    try:

        # Save user message
        save_message(
            chat_id=request.chat_id,
            role="user",
            content=request.message,
        )

        # Get conversation history
        history = get_history(request.chat_id)

        # Generate AI response
        response = await generate_response(
            conversation_history=history,
        )

        # Save AI response
        save_message(
            chat_id=request.chat_id,
            role="model",
            content=response,
        )

        return {
            "message": request.message,
            "response": response,
        }

    except RuntimeError as e:

        logger.error(
            "Chat generation error: %s",
            e,
        )

        return JSONResponse(
            status_code=503,
            content={
                "message": "Unable to generate a response right now.",
                "error": str(e),
            },
        )

    except Exception as e:

        logger.exception(
            "Unexpected /chat error: %s",
            e,
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "An internal server error occurred.",
            },
        )


# =========================
# Telegram Bot Information
# =========================

@app.get("/telegram/bot")
async def telegram_bot():

    logger.info(
        "Getting Telegram bot information"
    )

    return await get_bot_info()


# =========================
# Telegram Webhook Information
# =========================

@app.get("/telegram/webhook-info")
async def webhook_info():

    logger.info(
        "Getting Telegram webhook information"
    )

    return await get_webhook_info()