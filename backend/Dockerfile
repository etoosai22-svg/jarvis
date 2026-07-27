# 빌드 컨텍스트는 저장소 루트다 — prompts/system_prompt.md를 함께 담아야 한다.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY backend/ backend/
COPY prompts/ prompts/

WORKDIR /srv/backend
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
