FROM python:3.11.2-slim-bullseye

WORKDIR /app
COPY . /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    discord.py[voice] \
    python-dotenv \
    pynamodb \
    boto3

CMD ["python3.11", "kancolle-bot.py"]