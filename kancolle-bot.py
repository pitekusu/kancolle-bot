import os
import asyncio
import boto3

from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks
from discord import app_commands, HTTPException, VoiceState

from pynamodb.attributes import ListAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.models import Model

import openai


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

#Fubuki_TOKEN = os.getenv('Fubuki_TOKEN')
#Kongou_TOKEN =  os.getenv('Kongou_TOKEN')
DevFubuki_TOKEN = os.getenv('DevFubuki_TOKEN')
openai.api_key = os.getenv("OPENAI_API_KEY")

textChannelId = int(os.getenv('textChannelId'))

JST = timezone(timedelta(hours=+9), 'JST')

# 00:00:00から23:00:00のリストを作成
dateTimeList = [f'{i:02d}:00:00' for i in range(24)]

intents = discord.Intents.all()
intents.message_content = True

fubuki_bot = discord.Client(intents=intents)
kongou_bot = discord.Client(intents=intents)

tree = app_commands.CommandTree(fubuki_bot)

message_log = [{"role": "system", "content": "You are a helpful assistant."}]

def send_message_chatgpt(message_log):
  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=message_log,
    max_tokens=2000,
    stop=None,
    temperature=0.7,
  )

  for choice in response.choices:
    if "text" in choice:
      return choice.text

  return response.choices[0].message.content

@fubuki_bot.event
async def on_ready():
    print(f'{fubuki_bot.user}BOT起動！')
    await tree.sync()
    await loop.start()
    await loop2.start()

@kongou_bot.event
async def on_ready():
    print(f'{kongou_bot.user}BOT起動！')


@fubuki_bot.event
async def on_message(message):

    if message.author == fubuki_bot.user:
        return

    if message.content.startswith('namae'):
        await message.channel.send(f'艦娘名GET: {Kanmusu.Name}')

    if message.content.startswith('kanshu'):
        await message.channel.send(f'艦種GET: {Kanmusu.Kanshu}')

    if message.content.startswith('jihou'):
        await play_sound()


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
    folder_name = Kanmusu.Name
    file_path = Path(os.path.join(folder_name, f"{jikan}.opus"))

    if voice_client is None:
        await alert_channel.send("しれいか～ん...吹雪もボイスチャンネルに呼んでほしいです...")
        return

    if file_path.exists():
        print(f"Dockerコンテナ内に音声ファイルが見つかりました。ファイルをロードします！ファイルは[{file_path}]です。]")
    else:
        print(f"コンテナ内に音声ファイルがありませんでした。S3からダウンロードします！ファイルは[{file_path}]です。")
        await download_from_s3(jikan,folder_name)

    voice_client.play(discord.FFmpegOpusAudio(file_path))
    int_Jikan = int(jikan)
    msg = Kanmusu.Jihou[int_Jikan]
    await alert_channel.send(msg)


async def download_from_s3(jikan,folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    file_path = os.path.join(folder_name, f"{jikan}.opus")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    obj = bucket.Object(file_path)
    response = obj.get()
    with open(file_path, "wb") as f:
        f.write(response['Body'].read())



@tree.command(name='join', description='艦娘がボイスチャンネルに来ます')
async def join_command(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    if not channel_name:
        await interaction.response.send_message(f'ボイスチャンネルに接続できませんでした。エラー: {e}')
        return

    try:
        fubuki_vc = await fubuki_bot.get_channel(channel_name.id).connect()
        kongou_vc = await kongou_bot.get_channel(channel_name.id).connect()
    except Exception as e:
        await interaction.response.send_message(f'ボイスチャンネルに接続できませんでした。エラー: {e}')
        return

    fubuki_msg = f'吹雪、{channel_name.name}鎮守府に着任します！'
    kongou_msg = f'金剛、{channel_name.name}鎮守府に着任します！'
    await interaction.response.send_message(fubuki_msg + '\n' + kongou_msg)

#tree.commandでtalkコマンドを定義し、send_message_chatgpt関数を呼び出してchatgptと会話する。会話はmessage_logで継続させる。
@tree.command(name='talk', description='ブッキーと会話します')
async def talk_command(interaction: discord.Interaction, message: str):
    global message_log
    
    if len(message_log) >= 20:
        message_log = message_log[10:]
    
    try:
        await interaction.response.defer()
        message_log.append({"role": "user", "content": message})
        response = send_message_chatgpt(message_log)
        message_log.append({"role": "assistant", "content": response})

        # 司令官の質問をEmbedに追加
        embed = discord.Embed(title=':man_pilot: 質問', description=message, color=0x00ff00)

        # 吹雪の回答をEmbedに追加
        embed.add_field(name=':woman_student: 回答', value=response, inline=False)

        # Embedを送信
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f'ブッキーと会話できませんでした。エラー: {e}')
        return


@tree.command(name='reset', description='ブッキーが記憶を失います')
async def reset_command(interaction: discord.Interaction):
    global message_log
    message_log = []

    # リセットメッセージの送信
    await interaction.response.send_message(
        ':zany face: 私は記憶を失いました。な～んにもわからないです！'
    )


loop2 = asyncio.get_event_loop()
#loop2.create_task(fubuki_bot.start(Fubuki_TOKEN))
#loop2.create_task(kongou_bot.start(Kongou_TOKEN))
loop2.create_task(fubuki_bot.start(DevFubuki_TOKEN))
loop2.run_forever()