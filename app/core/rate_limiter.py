import time

from collections import defaultdict


# Maximum number of messages allowed
MAX_REQUESTS = 10

# Time window in seconds
WINDOW_SECONDS = 60


user_requests: dict[int, list[float]] = defaultdict(list)


def is_rate_limited(chat_id: int) -> bool:

    current_time = time.time()

    requests = user_requests[chat_id]

    # Remove requests outside the current window
    requests[:] = [
        request_time
        for request_time in requests
        if current_time - request_time < WINDOW_SECONDS
    ]

    if len(requests) >= MAX_REQUESTS:
        return True

    requests.append(current_time)

    return False