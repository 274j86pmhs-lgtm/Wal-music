import os
import asyncio
import discord
from discord.ext import commands
import yt_dlp
import nacl.secret
import nacl.utils
from flask import Flask
from threading import Thread

# --- إعداد سيرفر الـ Flask الوهمي لمنع انطفاء المنصة ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
# ---------------------------------------------

# إعدادات البحث المباشر بالاسم لتجاوز الحظر
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch', # البحث التلقائي بالاسم
    'source_address': '0.0.0.0',
    'geo_bypass': True,
    'cookiefile': 'cookies.txt',
    'extractor_args': {'youtube': {'player_client': ['mweb']}},
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Unknown Title')
        self.url = data.get('url')

    @classmethod
    async def create_source(cls, search: str, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        
        # تجنب استخدام الروابط نهائياً وإجبار البوت على البحث النصي
        if search.startswith("http://") or search.startswith("https://"):
            search = f"ytsearch:{search}" # حتى لو حطت رابط بالغلط يحوله بحث
            
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data.get('url')
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicControlView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="▶️")
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_paused():
            self.ctx.voice_client.resume()
            await interaction.response.send_message("تم استئناف التشغيل 🎶", ephemeral=True)
        else:
            await interaction.response.send_message("المشغل ليس في حالة إيقاف مؤقت.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⏸️")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            await interaction.response.send_message("تم إيقاف التشغيل مؤقتاً ⏸️", ephemeral=True)
        else:
            await interaction.response.send_message("لا يوجد شي يعمل حالياً.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client:
            await self.ctx.voice_client.disconnect()
            try:
                await interaction.message.delete()
            except:
                pass
            await interaction.response.send_message("تم إيقاف البوت وخروجه ⏹️", ephemeral=True)
        else:
            await interaction.response.send_message("البوت ليس في روم صوتي.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji="❤️")
    async def like_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("تم حفظ الأغنية في مفضلتك 🤍🦢", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="?", intents=discord.Intents.all())

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (Ready to play!)")

@bot.command(name="play")
async def play(ctx: commands.Context, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("عليك الدخول إلى روم صوتي أولاً! 🦢")

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    async with ctx.typing():
        try:
            player = await YTDLSource.create_source(search, loop=bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        except Exception as e:
            return await ctx.send(f"عذراً، صار فيه خطأ أثناء البحث عن الأغنية: {e}")

    view = MusicControlView(ctx)
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"`{player.title}`",
        color=0x5865F2
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed, view=view)

# --- تشغيل البوت رسمياً ---
bot.run(os.getenv("DISCORD_TOKEN"))
