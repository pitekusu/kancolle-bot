import os
import discord


TOKEN = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True
tree = app_commands.CommandTree(client)

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
            await message.channel.send("司令官はボイスチャンネルに接続していないようです。")
            return
    # ボイスチャンネルに接続する
    await message.author.voice.channel.connect()

    await message.channel.send("接続しました！")

@tree.command(name="test",description="テストコマンドです。")
async def test_command(interaction: discord.Interaction,text:str="てすと"):#デフォルト値を指定
    await interaction.response.send_message(text,ephemeral=True)

client.run(TOKEN)
