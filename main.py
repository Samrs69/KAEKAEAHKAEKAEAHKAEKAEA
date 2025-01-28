import os
import sys
import json
import asyncio
import platform
import requests
import websockets
from colorama import init, Fore
from keep_alive import keep_alive

init(autoreset=True)

import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

queue = []
autoplay = True

@bot.event
async def on_ready():
    print(f'Bot is ready: {bot.user.name}')

@bot.command(name='join')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You need to be in a voice channel.")
        return
    channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name='play')
async def play(ctx, *, query):
    if not ctx.message.author.voice:
        await ctx.send("You need to be in a voice channel.")
        return

    if not ctx.voice_client:
        await join(ctx)

    if not query.startswith("http"):
        await ctx.send(f"Searching for: **{query}**")
        ytdl_query_options = {
            'format': 'bestaudio/best',
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'quiet': True
        }
        ytdl_query = youtube_dl.YoutubeDL(ytdl_query_options)
        info = await bot.loop.run_in_executor(None, lambda: ytdl_query.extract_info(f"ytsearch:{query}", download=False))
        if 'entries' in info:
            url = info['entries'][0]['url']
        else:
            await ctx.send("No results found.")
            return
    else:
        url = query

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print('Error: %s' % e) if e else None)
    
    await ctx.send(f'Now playing: **{player.title}**')

    # حل مشكلة توقف الأغنية بعد نصفها
    await ensure_continuous_playback(ctx)

async def ensure_continuous_playback(ctx):
    while ctx.voice_client.is_playing():
        await asyncio.sleep(1)
    await asyncio.sleep(2)  # إضافة تأخير بسيط لمراجعة حالة البوت
    if not ctx.voice_client.is_playing():
        await ctx.voice_client.disconnect()

@bot.command(name='pause')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send("Nothing is playing.")

@bot.command(name='resume')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        voice_client.resume()
    else:
        await ctx.send("The song is not paused.")

@bot.command(name='stop')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("Nothing is playing.")

@bot.command(name='skip')
async def skip(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("Nothing is playing.")

@bot.command(name='queue')
async def show_queue(ctx):
    if queue:
        queue_list = "\n".join(queue)
        await ctx.send(f"Queue:\n{queue_list}")
    else:
        await ctx.send("The queue is empty.")

@bot.command(name='autoplay')
async def toggle_autoplay(ctx):
    global autoplay
    autoplay = not autoplay
    status = "enabled" if autoplay else "disabled"
    await ctx.send(f"Autoplay is now {status}.")

@bot.command(name='commands')
async def commands_list(ctx):
    commands_info = """
    **Commands List:**
    !join - Join a voice channel
    !leave - Leave the voice channel
    !play <song_name_or_url> - Play a song
    !pause - Pause the song
    !resume - Resume the song
    !stop - Stop the song
    !skip - Skip the song
    !queue - Show the song queue
    !autoplay - Toggle autoplay

    created by Mishary :}
    """
    await ctx.send(commands_info)

bot.run('')


keep_alive()
asyncio.run(run_onliner())
