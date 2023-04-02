import os
import boto3

from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

import discord
from discord.ext import tasks
from discord import app_commands

from pynamodb.attributes import ListAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.models import Model


load_dotenv()


class kancolle_table(Model):
    class Meta:
        aws_access_key_id = os.getenv('aws_access_key_id')
        aws_secret_access_key = os.getenv('aws_secret_access_key')
        region = 'ap-northeast-1'
        table_name = "kancolle_table"
    Id = NumberAttribute(hash_key=True)
    Name = UnicodeAttribute(null=False)
    Kanshu = UnicodeAttribute(null=False)
    Jihou = ListAttribute(null=False)


# 吹雪ちゃん(Id=0)の情報を取得
Kanmusu = kancolle_table.get(0)

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
s3 = boto3.resource('s3',
                    aws_access_key_id=os.getenv('aws_access_key_id'),
                    aws_secret_access_key=os.getenv('aws_secret_access_key'))

TOKEN = os.getenv('TOKEN')
textChannelId = int(os.getenv('textChannelId'))


JST = timezone(timedelta(hours=+9), 'JST')

# 00:00:00から23:00:00のリストを作成
dateTimeList = [f'{i:02d}:00:00' for i in range(24)]

intents = discord.Intents.all()
intents.message_content = True

fubuki_bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(fubuki_bot)


@fubuki_bot.event
async def on_ready():
    print(f'{fubuki_bot.user}BOT起動！')
    await tree.sync()
    await loop.start()


@fubuki_bot.event
async def on_message(message):

    if message.author == fubuki_bot.user:
        return

    if message.content.startswith('namae'):
        await message.channel.send(f'艦娘名GET: {Kanmusu.Name}')

    if message.content.startswith('kanshu'):
        await message.channel.send(f'艦種GET: {Kanmusu.Kanshu}')

    if message.content.startswith('jihou'):
        jikan = datetime.now(JST).strftime('%H')
        alert_channel = fubuki_bot.get_channel(textChannelId)
        if discord.utils.get(fubuki_bot.voice_clients) is None:
            await alert_channel.send("しれいか～ん...吹雪もボイスチャンネルに呼んでほしいです...")
            return
        voice_client = discord.utils.get(fubuki_bot.voice_clients)
        path = f'./{jikan}.opus'
        if os.path.exists(path) is True:
            print("ファイルがあったよ")
            voice_client.play(discord.FFmpegOpusAudio(f"{jikan}.opus"))
            return
        print("ファイルがなかったよ")
        bucket = s3.Bucket(S3_BUCKET_NAME)
        obj = bucket.Object(f'fubuki/{jikan}.opus')
        response = obj.get()
        with open(f"{jikan}.opus", "wb") as f:
            f.write(response['Body'].read())
        voice_client.play(discord.FFmpegOpusAudio(f"{jikan}.opus"))


@fubuki_bot.event
async def on_voice_state_update(member, before, after):
    alert_channel = fubuki_bot.get_channel(textChannelId)
    if before.channel != after.channel:
        if member.bot:
            return
        if before.channel and after.channel:
            msg = f':arrows_counterclockwise: {member.display_name} 司令官が {before.channel.name} 鎮守府から {after.channel.name} 鎮守府に異動しました！'
            await alert_channel.send(msg)
        elif before.channel:
            msg = f':outbox_tray: {member.display_name} 司令官が {before.channel.name} 鎮守府から離任されました…'
            await alert_channel.send(msg)
        elif after.channel:
            msg = f':inbox_tray: {member.display_name} 司令官が {after.channel.name} 鎮守府に着任しました！'
            await alert_channel.send(msg)


@tasks.loop(seconds=1)
async def loop():
    now = datetime.now(JST).strftime('%H:%M:%S')
    if now in dateTimeList:
        await play_sound()


async def play_sound():
    jikan = datetime.now(JST).strftime('%H')
    alert_channel = fubuki_bot.get_channel(textChannelId)
    voice_client = discord.utils.get(fubuki_bot.voice_clients)
    path = Path(f'./{jikan}.opus')

    if voice_client is None:
        await alert_channel.send("しれいか～ん...吹雪もボイスチャンネルに呼んでほしいです...")
        return

    if path.exists():
        print("コンテナ内にファイルがあったので、ローカルから読み込むよ。")
    else:
        print("コンテナ内にファイルがなかったので、S3からダウンロードするよ。")
        await download_from_s3(jikan)

    voice_client.play(discord.FFmpegOpusAudio(path))
    int_Jikan = int(jikan)
    msg = Kanmusu.Jihou[int_Jikan]
    await alert_channel.send(msg)


async def download_from_s3(jikan):
    bucket = s3.Bucket(S3_BUCKET_NAME)
    obj = bucket.Object(f'fubuki/{jikan}.opus')
    response = obj.get()
    with open(f"{jikan}.opus", "wb") as f:
        f.write(response['Body'].read())


@tree.command(name='join', description='ブッキーがボイスチャンネルに来ます')
async def join_command(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    if not channel_name:
        await interaction.response.send_message('ボイスチャンネルに接続できませんでした。')
        return

    try:
        vc = await channel_name.connect()
    except Exception as e:
        await interaction.response.send_message(f'ボイスチャンネルに接続できませんでした。エラー: {e}')
        return

    msg = f'吹雪、{channel_name.name}鎮守府に着任します！'
    await interaction.response.send_message(msg)

fubuki_bot.run(TOKEN)
