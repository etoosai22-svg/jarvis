from datetime import UTC, datetime


def utcnow() -> datetime:
    """모델의 naive `DateTime` 컬럼에 맞춘 UTC 현재 시각.

    `datetime.utcnow()`는 3.12에서 deprecated이고, aware datetime을 그대로 넣으면
    PostgreSQL의 `TIMESTAMP WITHOUT TIME ZONE`에서 오프셋이 잘려나간다.
    """
    return datetime.now(UTC).replace(tzinfo=None)
