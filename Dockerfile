FROM python:3.11.2-slim-bullseye
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY . /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir \
    discord.py[voice] \
    python-dotenv \
    pynamodb \
    boto3 \
    openai

ENTRYPOINT ["python3.11", "kancolle-bot.py"]