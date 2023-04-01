import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime, timedelta, timezone
from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute, ListAttribute

# ECS環境ではdotenv不要
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

TOKEN = os.getenv('TOKEN')
textChannelId = int(os.getenv('textChannelId'))

JST = timezone(timedelta(hours=+9), 'JST')

# 1時間ごとのdateTimeListを作成
dateTimeList = [f'{i:02d}' for i in range(25)]

#MY_GUILD_ID = os.environ['MY_GUILD_ID']

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

    if message.content == "!join":
        if message.author.voice is None:
            await message.channel.send('司令官はボイスチャンネルに接続していないようです。')
            return
    # ボイスチャンネルに接続する
        await message.author.voice.channel.connect()
        await message.channel.send('接続しました！')


@fubuki_bot.event
async def on_voice_state_update(member, before, after):
    alert_channel = fubuki_bot.get_channel(textChannelId)
    if (before.channel != after.channel):
        if member.bot == True:
            return
        if before.channel is None:
            msg = f'{member.name} 司令官が {after.channel.name} 鎮守府に着任しました！'
            await alert_channel.send(msg)
        elif after.channel is None:
            msg = f'{member.name} 司令官が {before.channel.name} 鎮守府から離任されました・・・'
            await alert_channel.send(msg)
        else:
            msg = f'{member.name} 司令官が {before.channel.name} 鎮守府から {after.channel.name} 鎮守府に異動しました！'
            await alert_channel.send(msg)


# 1時間毎に時報を送信する
@tasks.loop(seconds=1)
async def loop():
    now = datetime.now(JST).strftime('%H:%M:%S')
    jikan = int(datetime.now(JST).strftime('%H'))
    if now in dateTimeList:
        alert_channel = fubuki_bot.get_channel(textChannelId)
        jikan = datetime.now(JST).strftime('%H')
        msg = Kanmusu.Jihou[jikan]
        await alert_channel.send(msg)


@tree.command(name='join', description='ブッキーがボイスチャンネルに来ます')
async def join_command(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    msg = f'吹雪、{channel_name.name}鎮守府に着任します！'
    await interaction.response.send_message(msg)
    await channel_name.connect()

fubuki_bot.run(TOKEN)
