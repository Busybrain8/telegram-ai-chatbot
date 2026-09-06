from sqlalchemy import delete, select

from app.database.database import SessionLocal
from app.database.models import Message, TelegramUpdate

from app.database.models import (
    Message,
    TelegramUpdate,
)

import logging

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20


def save_message(
    chat_id: int,
    role: str,
    content: str,
) -> None:

    with SessionLocal() as session:

        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
        )

        session.add(message)
        session.commit()


def get_history(
    chat_id: int,
    limit: int = 20,
) -> list[dict]:

    with SessionLocal() as session:

        statement = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = session.scalars(statement).all()

        messages = list(reversed(messages))

        return [
            {
                "role": message.role,
                "parts": [
                    {
                        "text": message.content,
                    }
                ],
            }
            for message in messages
        ]

def clear_history(
    chat_id: int,
) -> None:

    with SessionLocal() as session:

        statement = (
            select(Message)
            .where(Message.chat_id == chat_id)
        )

        messages = session.scalars(statement).all()

        for message in messages:
            session.delete(message)

        session.commit()


def get_recent_messages(
    chat_id: int,
    limit: int = 10,
) -> list[Message]:

    with SessionLocal() as session:

        statement = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        messages = session.scalars(statement).all()

        return list(reversed(messages))

def update_already_processed(
    update_id: int,
) -> bool:

    with SessionLocal() as session:

        statement = (
            select(TelegramUpdate)
            .where(
                TelegramUpdate.update_id == update_id
            )
        )

        existing_update = session.scalars(
            statement
        ).first()

        return existing_update is not None


def mark_update_processed(
    update_id: int,
) -> None:

    with SessionLocal() as session:

        update = TelegramUpdate(
            update_id=update_id,
        )

        session.add(update)
        session.commit()

def update_already_processed(
    update_id: int,
) -> bool:

    with SessionLocal() as session:

        statement = (
            select(TelegramUpdate)
            .where(
                TelegramUpdate.update_id == update_id
            )
        )

        existing_update = session.scalars(
            statement
        ).first()

        return existing_update is not None


def mark_update_processed(
    update_id: int,
) -> None:

    with SessionLocal() as session:

        update = TelegramUpdate(
            update_id=update_id,
        )

        session.add(update)
        session.commit()