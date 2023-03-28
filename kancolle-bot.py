import os
from dotenv import load_dotenv
import discord
from discord import app_commands

# ECS環境ではdotenv不要
load_dotenv()

TOKEN = os.environ['TOKEN']
MY_GUILD_ID = os.environ['MY_GUILD_ID']

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await tree.sync(guild=discord.Object(id=MY_GUILD_ID))


@client.event
async def on_message(message):
    if message.author == client.user:
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


@tree.command(name='join', description='ブッキーがボイスチャンネルに来ます', guild=discord.Object(id=MY_GUILD_ID))
async def join_command(interaction: discord.Interaction, channel_name: discord.VoiceChannel):
    await interaction.response.send_message('チャンネルに参加します！')
    await channel_name.connect()

client.run(TOKEN)
