from app.core import rate_limiter


def test_user_is_not_rate_limited_initially():
    rate_limiter.user_requests.clear()

    assert rate_limiter.is_rate_limited(12345) is False


def test_user_is_rate_limited_after_maximum_requests():
    rate_limiter.user_requests.clear()

    chat_id = 12345

    for _ in range(rate_limiter.MAX_REQUESTS):
        assert rate_limiter.is_rate_limited(chat_id) is False

    assert rate_limiter.is_rate_limited(chat_id) is True


def test_different_users_have_separate_limits():
    rate_limiter.user_requests.clear()

    user_one = 111
    user_two = 222

    for _ in range(rate_limiter.MAX_REQUESTS):
        rate_limiter.is_rate_limited(user_one)

    assert rate_limiter.is_rate_limited(user_one) is True
    assert rate_limiter.is_rate_limited(user_two) is False