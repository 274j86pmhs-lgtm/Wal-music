import os
import discord
from discord.ext import commands
import wavelink

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        nodes = [wavelink.Node(uri="http://localhost:2333", password="youshallnotpass")]
        await wavelink.Pool.init(nodes=nodes)

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (Ready to play!)")

@bot.command(name="play")
async def play(ctx: commands.Context, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("عليك الدخول إلى روم صوتي أولاً! 🦢")
    player = ctx.voice_client
    if not player:
        player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    tracks = await wavelink.Playable.search(search)
    if not tracks:
        return await ctx.send("ما لقيت نتائج لهذه الأغنية!")
    track = tracks[0]
    await player.play(track)
    await ctx.send(f"🎵 **Now Playing**\n`{track.title}`")

# سحب التوكن بأمان من إعدادات الاستضافة
bot.run(os.getenv("DISCORD_TOKEN"))
