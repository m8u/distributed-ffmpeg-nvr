from datetime import timedelta


def get_reconnection_interval(attempt: int) -> timedelta:
    if attempt <= 3:
        return timedelta(seconds=1)
    if attempt <= 10:
        return timedelta(seconds=10)

    return timedelta(seconds=30)
