TELEGRAM_MESSAGE_LIMIT = 4096


def split_message(
    text: str,
    max_length: int = TELEGRAM_MESSAGE_LIMIT,
) -> list[str]:

    if len(text) <= max_length:
        return [text]

    chunks = []

    while len(text) > max_length:

        split_at = text.rfind(
            "\n",
            0,
            max_length,
        )

        if split_at == -1:
            split_at = text.rfind(
                " ",
                0,
                max_length,
            )

        if split_at == -1:
            split_at = max_length

        chunks.append(
            text[:split_at].strip()
        )

        text = text[split_at:].strip()

    if text:
        chunks.append(text)

    return chunks