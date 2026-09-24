from app.utils.telegram_utils import split_message


def test_short_message_is_not_split():
    text = "Hello, Moses!"

    result = split_message(text)

    assert result == [text]


def test_long_message_is_split():
    text = "a" * 100

    result = split_message(text, max_length=20)

    assert len(result) == 5
    assert all(len(chunk) <= 20 for chunk in result)


def test_message_prefers_newline_when_splitting():
    text = "first line\nsecond line\nthird line"

    result = split_message(text, max_length=20)

    assert len(result) > 1
    assert all(len(chunk) <= 20 for chunk in result)


def test_message_prefers_spaces_when_no_newline_exists():
    text = "one two three four five six seven"

    result = split_message(text, max_length=15)

    assert len(result) > 1
    assert all(len(chunk) <= 15 for chunk in result)


def test_exact_limit_is_not_split():
    text = "a" * 4096

    result = split_message(text)

    assert result == [text]