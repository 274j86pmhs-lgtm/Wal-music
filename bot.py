import os
import discord
from discord.ext import commands
import wavelink

class MusicControlView(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="▶️")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player:
            await self.player.pause(False)
            await interaction.response.send_message("تم استئناف التشغيل 🎶", ephemeral=True)
        else:
            await interaction.response.send_message("لا يوجد مشغل نشط حالياً.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player:
            await self.player.pause(True)
            await interaction.response.send_message("تم إيقاف التشغيل مؤقتاً ⏸️", ephemeral=True)
        else:
            await interaction.response.send_message("لا يوجد مشغل نشط حالياً.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player:
            await self.player.stop()
            await interaction.message.delete()
            await interaction.response.send_message("تم إيقاف البوت وخروجه ⏹️", ephemeral=True)
        else:
            await interaction.response.send_message("البوت ليس في حالة تشغيل حالياً.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji="❤️")
    async def like_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("تم حفظ الأغنية في مفضلتك 🤍🦢", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="?", intents=discord.Intents.all())

    async def setup_hook(self):
        node = wavelink.Node(uri="https://lavalink.darrennathanael.com:443", password="youshallnotpass")
        await wavelink.Pool.connect(nodes=[node], client=self)
        print("Connected to Lavalink Node successfully!")

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
    
    view = MusicControlView(player)
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"`{track.title}`",
        color=0x5865F2
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed, view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
