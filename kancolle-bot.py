import os
from dotenv import load_dotenv
import discord
from discord import app_commands

# ECS環境ではdotenv不要
load_dotenv()

TOKEN = os.getenv('TOKEN')
textChannelId = int(os.getenv('textChannelId'))


#MY_GUILD_ID = os.environ['MY_GUILD_ID']

intents = discord.Intents.all()
intents.message_content = True

fubuki_bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(fubuki_bot)


@fubuki_bot.event
async def on_ready():
    print(f'{fubuki_bot.user}BOT起動！')
#   await tree.sync(guild=discord.Object(id=MY_GUILD_ID))
    await tree.sync()


@fubuki_bot.event
async def on_message(message):
    if message.author == fubuki_bot.user:
        return

    if message.content.startswith('bukki'):
        await message.channel.send('隠しブッキー!')

    if message.content == "!join":
        if message.author.voice is None:
            await message.channel.send('司令官はボイスチャンネルに接続していないようです。')
            return
    # ボイスチャンネルに接続する
        await message.author.voice.channel.connect()
        await message.channel.send('接続しました！')


@fubuki_bot.event
async def on_voice_state_update(member, before, after):
    if (before.channel != after.channel):
        if member.bot == True:
            return
        alert_channel = fubuki_bot.get_channel(textChannelId)
        if before.channel is None:
            msg = f'{member.name} 司令官が {after.channel.name} 鎮守府に着任しました！'
            await alert_channel.send(msg)
        elif after.channel is None:
            msg = f'{member.name} 司令官が {before.channel.name} 鎮守府から離任されました・・・'
            await alert_channel.send(msg)
        else:
            msg = f'{member.name} 司令官が {before.channel.name} 鎮守府から {after.channel.name} 鎮守府に異動しました！'
            await alert_channel.send(msg)


# @tree.command(name='join', description='ブッキーがボイスチャンネルに来ます', guild=discord.Object(id=MY_GUILD_ID))
@tree.command(name='join', description='ブッキーがボイスチャンネルに来ます')
async def join_command(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    msg = f'吹雪、{channel_name.name}鎮守府に着任します！'
    await interaction.response.send_message(msg)
    await channel_name.connect()

fubuki_bot.run(TOKEN)
