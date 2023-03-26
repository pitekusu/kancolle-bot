FROM python:3.11.2-slim-bullseye

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y ffmpeg

RUN python -m pip install \
    --upgrade pip \
    --upgrade setuptools \
    discord.py[voice]

CMD ["python3.11", "kancolle-bot.py"]