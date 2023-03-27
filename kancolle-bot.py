import os
import discord


TOKEN = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('hello'):
        await message.channel.send('隠しブッキー!')
        
    if message.content == "!join":
        if message.author.voice is None:
            await message.channel.send("あなたはボイスチャンネルに接続していません。")
            return
    # ボイスチャンネルに接続する
    await message.author.voice.channel.connect()

    await message.channel.send("接続しました。")

client.run(TOKEN)
