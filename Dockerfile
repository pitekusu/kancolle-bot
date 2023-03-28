FROM python:3.11.2-slim-bullseye

WORKDIR /app
COPY . /app

#RUN apt-get update && apt-get install -y ffmpeg

#ECS環境ではdotenv不要
RUN python -m pip install \
    discord.py[voice] \
    python-dotenv



CMD ["python3.11", "kancolle-bot.py"]