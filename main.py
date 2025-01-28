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
import youtube_dl

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Set up youtube_dl options
ytdl_format_options = {
    'format': 'bestaudio',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'quiet': True,
}
ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None

    def add_to_queue(self, song):
        self.queue.append(song)

    def get_queue(self):
        return self.queue

music_player = MusicPlayer()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='join')
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("You are not connected to a voice channel.")

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name='play')
async def play(ctx, *, url):
    if not ctx.voice_client:
        await ctx.invoke(join)

    async with ctx.typing():
        info = ytdl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        voice_client = ctx.voice_client
        voice_client.play(discord.FFmpegPCMAudio(URL, **ffmpeg_options))
        music_player.add_to_queue(info['title'])
        await ctx.send(f'Now playing: **{info["title"]}**')

@bot.command(name='queue')
async def queue(ctx):
    if music_player.get_queue():
        embed = discord.Embed(title="Song Queue", color=discord.Color.blue())
        for idx, song in enumerate(music_player.get_queue(), start=1):
            embed.add_field(name=f"Song {idx}", value=song, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("The queue is currently empty.")

@bot.command(name='skip')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song.")
    else:
        await ctx.send("There's no song to skip.")

bot.run('MTMzMzYzOTkwNjg2OTkwMzM2MA.GCxvjx.S7vnJRw7BxrSmfbfZGXXgq7-5yBbt9SSv32JEM')


keep_alive()
asyncio.run(run_onliner())
